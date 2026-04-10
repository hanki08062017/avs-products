import json
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.shortcuts import render, redirect

API_KEY = 'avs-wallet-api-key-2024'


def _api_auth(request):
    return request.headers.get('X-API-Key') == API_KEY


def _mgmt_auth(request):
    return request.session.get('mgmt_logged_in') is True


def _badge(value, mapping):
    """Return a dict with badge class based on value mapping."""
    cls = mapping.get(value, 'bg-secondary')
    return {'value': value, 'badge': True, 'badge_class': cls}


def _cell(value):
    return {'value': value if value not in (None, '') else '—', 'badge': False}


# ── Status badge maps ────────────────────────────────────────────────────────
ORDER_STATUS_MAP = {
    'Delivered': 'bg-success', 'Cancelled': 'bg-danger',
    'Shipped': 'bg-info text-dark', 'Confirmed': 'bg-primary',
    'Processing': 'bg-warning text-dark', 'Placed': 'bg-secondary',
}
PAYMENT_STATUS_MAP = {
    'Successful': 'bg-success', 'Failed': 'bg-danger',
    'Pending': 'bg-warning text-dark', 'Cancelled': 'bg-secondary',
}
ACTIVE_MAP = {'Active': 'bg-success', 'Inactive': 'bg-secondary'}
BOOL_MAP = {True: 'bg-success', False: 'bg-secondary'}


def mgmt_login(request):
    if _mgmt_auth(request):
        return redirect('mgmt_dashboard')
    error = None
    if request.method == 'POST':
        from management.models import ManagementUser
        from django.utils import timezone
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            user = ManagementUser.objects.get(username=username, password=password)
            if user.status != 'Active':
                error = 'Your account is inactive. Contact administrator.'
            else:
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                request.session['mgmt_logged_in'] = True
                request.session['mgmt_username'] = user.username
                request.session['mgmt_name'] = f'{user.first_name} {user.last_name}'
                request.session['mgmt_role'] = user.role
                return redirect('mgmt_dashboard')
        except ManagementUser.DoesNotExist:
            error = 'Invalid username or password.'
    return render(request, 'management/login.html', {'error': error})


def mgmt_logout(request):
    for key in ('mgmt_logged_in', 'mgmt_username', 'mgmt_name', 'mgmt_role'):
        request.session.pop(key, None)
    return redirect('mgmt_login')


def mgmt_dashboard(request):
    if not _mgmt_auth(request):
        return redirect('mgmt_login')

    from management.models import Product, Order, Payment, Wallet
    from customer.models import Customer
    from seller.models import Staff

    stats = [
        {'label': 'Total Orders', 'value': Order.objects.count(), 'icon': 'bi-cart3', 'bg': '#ede9fe', 'color': '#7c3aed'},
        {'label': 'Total Products', 'value': Product.objects.count(), 'icon': 'bi-box-seam', 'bg': '#dbeafe', 'color': '#2563eb'},
        {'label': 'Customers', 'value': Customer.objects.count(), 'icon': 'bi-people', 'bg': '#dcfce7', 'color': '#16a34a'},
        {'label': 'Staff', 'value': Staff.objects.count(), 'icon': 'bi-person-badge', 'bg': '#fef9c3', 'color': '#ca8a04'},
        {'label': 'Wallets', 'value': Wallet.objects.count(), 'icon': 'bi-wallet2', 'bg': '#fce7f3', 'color': '#db2777'},
        {'label': 'Pending Orders', 'value': Order.objects.filter(order_status='Placed').count(), 'icon': 'bi-hourglass-split', 'bg': '#ffedd5', 'color': '#ea580c'},
        {'label': 'Delivered', 'value': Order.objects.filter(order_status='Delivered').count(), 'icon': 'bi-check-circle', 'bg': '#dcfce7', 'color': '#16a34a'},
        {'label': 'Cancelled', 'value': Order.objects.filter(order_status='Cancelled').count(), 'icon': 'bi-x-circle', 'bg': '#fee2e2', 'color': '#dc2626'},
    ]

    recent_orders = Order.objects.order_by('-placed_at')[:8]
    recent_customers = Customer.objects.order_by('-created_at')[:8]

    return render(request, 'management/dashboard.html', {
        'stats': stats,
        'recent_orders': recent_orders,
        'recent_customers': recent_customers,
    })


def mgmt_table(request, table):
    if not _mgmt_auth(request):
        return redirect('mgmt_login')

    from management.models import (
        BusinessDetail, GSTDetail, ProductCategory, Product,
        Order, Payment, UnitOfMeasurement, Wallet, WalletTransaction,
        Refund, DeliverySettings, DeliveryZone, WalletAPIConfig
    )
    from customer.models import Customer
    from seller.models import Staff

    ctx = {'table': table}

    if table == 'business':
        ctx.update(title='Business Details', icon='bi-building',
                   filter_field='status', filter_label='Status', filter_options=['Active', 'Inactive'],
                   columns=['Name', 'Code', 'Type', 'Mode', 'Address', 'City', 'State', 'PIN', 'Country', 'Status', 'Created', 'Modified'])
        ctx['rows'] = [[{**_cell(o.business_name), 'pk': o.serial_no}, _cell(o.code), _cell(o.business_type),
                        _cell(o.mode), _cell(o.address), _cell(o.city), _cell(o.state), _cell(o.pin), _cell(o.country),
                        _badge(o.status, ACTIVE_MAP),
                        _cell(o.created_at.strftime('%d %b %Y %H:%M')),
                        _cell(o.modified_at.strftime('%d %b %Y %H:%M'))] for o in BusinessDetail.objects.all()]

    elif table == 'gst':
        ctx.update(title='GST Details', icon='bi-receipt', filter_field=None,
                   columns=['GST Number', 'PAN', 'Business', 'Reg Date', 'Valid Till', 'Address', 'City', 'PIN', 'Country', 'Status', 'Created By', 'Created', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(o.gst_number), 'pk': o.serial_no}, _cell(o.pan), _cell(str(o.business_code)),
                        _cell(o.reg_date), _cell(o.valid_till), _cell(o.address), _cell(o.city), _cell(o.pin), _cell(o.country),
                        _badge(o.status, ACTIVE_MAP),
                        _cell(o.created_by), _cell(o.created_at.strftime('%d %b %Y %H:%M')),
                        _cell(o.modified_by), _cell(o.modified_at.strftime('%d %b %Y %H:%M'))] for o in GSTDetail.objects.all()]

    elif table == 'categories':
        ctx.update(title='Product Categories', icon='bi-tags', filter_field=None,
                   columns=['Category', 'Sub Category', 'HSN', 'SGST %', 'CGST %', 'GST %', 'Seller', 'Created', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(o.category), 'pk': o.id}, _cell(o.sub_category), _cell(o.hsn),
                        _cell(o.sgst), _cell(o.cgst), _cell(o.gst),
                        _cell(o.created_by), _cell(o.created_at.strftime('%d %b %Y %H:%M')),
                        _cell(o.modified_by), _cell(o.modified_at.strftime('%d %b %Y %H:%M'))] for o in ProductCategory.objects.all()]

    elif table == 'products':
        ctx.update(title='Products', icon='bi-box-seam',
                   filter_field='status', filter_label='Status', filter_options=['Active', 'Inactive'],
                   columns=['ID', 'Name', 'Category', 'MRP', 'Price', 'Cost', 'Stock', 'Business', 'Status', 'Created By', 'Created', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(o.id), 'pk': o.id}, _cell(o.product_name), _cell(str(o.product_category)),
                        _cell(f'\u20b9{o.mrp}'), _cell(f'\u20b9{o.selling_price}'), _cell(f'\u20b9{o.cost_price}'), _cell(o.stock),
                        _cell(str(o.business_code) if o.business_code else '\u2014'),
                        _badge(o.status, ACTIVE_MAP),
                        _cell(o.created_by), _cell(o.created_at.strftime('%d %b %Y %H:%M')),
                        _cell(o.modified_by), _cell(o.modified_at.strftime('%d %b %Y %H:%M') if o.modified_at else '\u2014')] for o in Product.objects.select_related('product_category', 'business_code').all()]

    elif table == 'orders':
        ctx.update(title='Orders', icon='bi-cart3',
                   filter_field='order_status', filter_label='Status',
                   filter_options=['Placed', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled'],
                   columns=['Order ID', 'Customer', 'Phone', 'Amount', 'Delivery', 'Sold By', 'Method', 'Order Status', 'Payment Status', 'Placed By', 'Placed At', 'Created By', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(o.order_id), 'pk': o.order_id}, _cell(o.customer_name), _cell(o.customer_phone),
                        _cell(f'\u20b9{o.total_amount}'), _cell(f'\u20b9{o.delivery_charge}'), _cell(o.sold_by),
                        _cell(o.payment_method),
                        _badge(o.order_status, ORDER_STATUS_MAP),
                        _badge(o.payment_status, PAYMENT_STATUS_MAP),
                        _cell(o.placed_by), _cell(o.placed_at.strftime('%d %b %Y %H:%M') if o.placed_at else '\u2014'),
                        _cell(o.created_by), _cell(o.modified_by),
                        _cell(o.modified_at.strftime('%d %b %Y %H:%M') if o.modified_at else '\u2014')] for o in Order.objects.all().order_by('-placed_at')]

    elif table == 'payments':
        ctx.update(title='Payments', icon='bi-credit-card',
                   filter_field='status', filter_label='Status',
                   filter_options=['Pending', 'Successful', 'Failed', 'Cancelled'],
                   columns=['Transaction ID', 'Order', 'Sold By', 'Amount', 'Mode', 'Type', 'Status', 'Created By', 'Created', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(o.transaction_id), 'pk': o.id}, _cell(str(o.reference_order_id)),
                        _cell(o.reference_order.sold_by if o.reference_order else '\u2014'),
                        _cell(f'\u20b9{o.amount}'), _cell(o.payment_mode), _cell(o.transaction_type),
                        _badge(o.status, PAYMENT_STATUS_MAP),
                        _cell(o.created_by), _cell(o.created_at.strftime('%d %b %Y %H:%M')),
                        _cell(o.modified_by), _cell(o.modified_at.strftime('%d %b %Y %H:%M'))] for o in Payment.objects.select_related('reference_order').all().order_by('-created_at')]

    elif table == 'refunds':
        ctx.update(title='Refunds', icon='bi-arrow-counterclockwise',
                   filter_field='refund_status', filter_label='Status',
                   filter_options=['Pending', 'Refunded', 'Rejected', 'Cancelled'],
                   columns=['ID', 'Order', 'Sold By', 'Amount', 'Mode', 'Refund Status', 'Refunded By', 'Refunded At', 'Created By', 'Created', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(o.id), 'pk': o.id}, _cell(str(o.reference_order_id)),
                        _cell(o.reference_order.sold_by if o.reference_order else '\u2014'),
                        _cell(f'\u20b9{o.amount}'), _cell(o.payment_mode),
                        _badge(o.refund_status, {'Refunded': 'bg-success', 'Pending': 'bg-warning text-dark', 'Rejected': 'bg-danger', 'Cancelled': 'bg-secondary'}),
                        _cell(o.refunded_by), _cell(o.refunded_at.strftime('%d %b %Y %H:%M') if o.refunded_at else '\u2014'),
                        _cell(o.created_by), _cell(o.created_at.strftime('%d %b %Y %H:%M')),
                        _cell(o.modified_by), _cell(o.modified_at.strftime('%d %b %Y %H:%M'))] for o in Refund.objects.select_related('reference_order').all().order_by('-created_at')]

    elif table == 'wallets':
        ctx.update(title='Wallets', icon='bi-wallet2', filter_field=None,
                   columns=['Wallet ID', 'Customer Name', 'Customer ID', 'Mobile', 'Type', 'Balance', 'Created'])
        ctx['rows'] = [[{**_cell(o.wallet_id), 'pk': o.wallet_id}, _cell(o.customer_name), _cell(o.customer_id),
                        _cell(o.customer_mobile), _cell(o.wallet_type),
                        _cell(f'\u20b9{o.wallet_amount}'),
                        _cell(o.created_at.strftime('%d %b %Y'))] for o in Wallet.objects.all()]

    elif table == 'wallet_transactions':
        ctx.update(title='Wallet Transactions', icon='bi-arrow-left-right',
                   filter_field='transaction_type', filter_label='Type',
                   filter_options=['Credit', 'Debit', 'Refund'],
                   columns=['Transaction ID', 'Customer', 'Customer ID', 'Type', 'Amount', 'For', 'Date'])
        ctx['rows'] = [[{**_cell(o.transaction_id), 'pk': o.id}, _cell(o.avs_customer_name), _cell(o.avs_customer_id),
                        _badge(o.transaction_type, {'Credit': 'bg-success', 'Debit': 'bg-danger', 'Refund': 'bg-info text-dark'}),
                        _cell(f'\u20b9{o.amount}'), _cell(o.transaction_for),
                        _cell(o.transaction_date.strftime('%d %b %Y') if o.transaction_date else '\u2014')] for o in WalletTransaction.objects.all().order_by('-transaction_date')]

    elif table == 'customers':
        ctx.update(title='Customers', icon='bi-people',
                   filter_field='status', filter_label='Status', filter_options=['Active', 'Inactive'],
                   columns=['Username', 'First Name', 'Last Name', 'Email', 'Phone', 'Status', 'Joined'])
        ctx['rows'] = [[{**_cell(o.username), 'pk': o.id}, _cell(o.first_name), _cell(o.last_name),
                        _cell(o.email), _cell(o.phone),
                        _badge('Active' if o.status else 'Inactive', ACTIVE_MAP),
                        _cell(o.created_at.strftime('%d %b %Y'))] for o in Customer.objects.all().order_by('-created_at')]

    elif table == 'staff_users':
        from seller.models import StaffUser
        ctx.update(title='Staff Users', icon='bi-person-circle',
                   filter_field=None,
                   columns=['Username', 'First Name', 'Last Name', 'Email', 'Phone', 'Status', 'Created'])
        ctx['rows'] = [[{**_cell(o.username), 'pk': o.id}, _cell(o.first_name), _cell(o.last_name),
                        _cell(o.email), _cell(o.phone),
                        _badge('Active' if o.status else 'Inactive', ACTIVE_MAP),
                        _cell(o.created_at.strftime('%d %b %Y'))] for o in StaffUser.objects.all().order_by('-created_at')]

    elif table == 'staff':
        ctx.update(title='Staff', icon='bi-person-badge',
                   filter_field='status', filter_label='Status', filter_options=['Active', 'Inactive'],
                   columns=['Staff ID', 'Name', 'Business', 'Role', 'Phone', 'Status', 'Created'])
        ctx['rows'] = [[{**_cell(o.staff_id), 'pk': o.staff_id}, _cell(o.full_name), _cell(str(o.business_code)),
                        _cell(o.role), _cell(o.phone),
                        _badge(o.status, ACTIVE_MAP),
                        _cell(o.created_at.strftime('%d %b %Y'))] for o in Staff.objects.select_related('business_code').all()]

    elif table == 'units':
        ctx.update(title='Units of Measurement', icon='bi-rulers', filter_field=None,
                   columns=['Name', 'Abbreviation', 'Seller', 'Created', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(o.name), 'pk': o.id}, _cell(o.abbreviation),
                        _cell(o.created_by), _cell(o.created_at.strftime('%d %b %Y %H:%M')),
                        _cell(o.modified_by), _cell(o.modified_at.strftime('%d %b %Y %H:%M'))] for o in UnitOfMeasurement.objects.all()]

    elif table == 'delivery_settings':
        ctx.update(title='Delivery Settings', icon='bi-gear', filter_field=None,
                   columns=['Business', 'Store Address', 'City', 'PIN', 'Delivery Free', 'Ship Free', 'Min Amount', 'Max Distance', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(str(o.business_code)), 'pk': o.id}, _cell(o.store_address), _cell(o.store_city), _cell(o.store_pin),
                        _badge('Yes' if o.delivery_free else 'No', {'Yes': 'bg-success', 'No': 'bg-secondary'}),
                        _badge('Yes' if o.ship_free else 'No', {'Yes': 'bg-success', 'No': 'bg-secondary'}),
                        _cell(f'\u20b9{o.min_amount_free_delivery}'), _cell(f'{o.max_distance_km} km'),
                        _cell(o.modified_by), _cell(o.modified_at.strftime('%d %b %Y %H:%M'))] for o in DeliverySettings.objects.all()]

    elif table == 'delivery_zones':
        ctx.update(title='Delivery Zones', icon='bi-map',
                   filter_field='status', filter_label='Status', filter_options=['Active', 'Inactive'],
                   columns=['Zone Name', 'Business', 'Pincode', 'Distance (km)', 'Base Charge', 'Status', 'Created By', 'Created', 'Modified By', 'Modified'])
        ctx['rows'] = [[{**_cell(o.zone_name), 'pk': o.id}, _cell(str(o.business_code)), _cell(o.pincode_to),
                        _cell(o.distance_range_km), _cell(f'\u20b9{o.base_charge}'),
                        _badge(o.status, ACTIVE_MAP),
                        _cell(o.created_by), _cell(o.created_at.strftime('%d %b %Y %H:%M')),
                        _cell(o.modified_by), _cell(o.modified_at.strftime('%d %b %Y %H:%M'))] for o in DeliveryZone.objects.select_related('business_code').all()]

    elif table == 'wallet_api_config':
        ctx.update(title='Wallet API Config', icon='bi-sliders',
                   filter_field='status', filter_label='Status', filter_options=['Active', 'Inactive'],
                   columns=['Config Name', 'Source', 'Endpoint', 'Method', 'Auth Type', 'Status'])
        ctx['rows'] = [[{**_cell(o.config_name), 'pk': o.id}, _cell(o.source_name),
                        _cell(o.endpoint_url[:40] + '...' if len(o.endpoint_url) > 40 else o.endpoint_url),
                        _cell(o.http_method), _cell(o.get_auth_type_display()),
                        _badge(o.status, ACTIVE_MAP)] for o in WalletAPIConfig.objects.all()]

    else:
        return redirect('mgmt_dashboard')

    return render(request, 'management/table.html', ctx)


# ── Form field definitions per table ────────────────────────────────────────
def _get_form_config(table):
    from management.models import BusinessDetail, ProductCategory, Order
    from customer.models import Customer
    from seller.models import StaffUser

    biz_opts = [{'value': o.code, 'label': str(o)} for o in BusinessDetail.objects.all()]
    cat_opts = [{'value': o.id, 'label': str(o)} for o in ProductCategory.objects.all()]
    order_opts = [{'value': o.order_id, 'label': o.order_id} for o in Order.objects.all()]
    staff_user_opts = [{'value': o.username, 'label': f'{o.username} — {o.first_name} {o.last_name}'} for o in StaffUser.objects.all()]

    STATUS = [{'value': 'Active', 'label': 'Active'}, {'value': 'Inactive', 'label': 'Inactive'}]
    MODE   = [{'value': 'Online', 'label': 'Online'}, {'value': 'Offline', 'label': 'Offline'}]
    BIZ_TYPE = [{'value': v, 'label': v} for v in ['Seller','Shop','Retailer','Service','Management']]
    WALLET_TYPE = [{'value': 'AVS', 'label': 'AVS'}, {'value': 'Other', 'label': 'Other'}]
    TXN_TYPE = [{'value': v, 'label': v} for v in ['Credit','Debit','Refund']]
    PAY_MODE = [{'value': v, 'label': v} for v in ['Cash','Card','UPI','Net Banking','Wallet']]
    ORDER_STATUS = [{'value': v, 'label': v} for v in ['Placed','Confirmed','Processing','Shipped','Delivered','Cancelled']]
    PAY_STATUS = [{'value': v, 'label': v} for v in ['Pending','Successful','Failed','Cancelled']]
    REFUND_STATUS = [{'value': v, 'label': v} for v in ['Pending','Refunded','Rejected','Cancelled']]
    ROLE = [{'value': v, 'label': v} for v in ['Super Admin','Admin','Viewer']]

    configs = {
        'business': {
            'title': 'Business', 'icon': 'bi-building', 'model': 'BusinessDetail', 'pk': 'serial_no',
            'fields': [
                {'name': 'business_name', 'label': 'Business Name', 'type': 'text', 'required': True},
                {'name': 'code', 'label': 'Code', 'type': 'text', 'required': True},
                {'name': 'business_type', 'label': 'Business Type', 'type': 'select', 'options': BIZ_TYPE, 'required': True},
                {'name': 'symbol', 'label': 'Symbol', 'type': 'text', 'required': True},
                {'name': 'mode', 'label': 'Mode', 'type': 'select', 'options': MODE, 'required': True},
                {'name': 'address', 'label': 'Address', 'type': 'text', 'required': True},
                {'name': 'city', 'label': 'City', 'type': 'text', 'required': True},
                {'name': 'state', 'label': 'State', 'type': 'text', 'required': True},
                {'name': 'pin', 'label': 'PIN', 'type': 'text', 'required': True},
                {'name': 'country', 'label': 'Country', 'type': 'text', 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': STATUS, 'required': True},
            ]
        },
        'gst': {
            'title': 'GST Detail', 'icon': 'bi-receipt', 'model': 'GSTDetail', 'pk': 'serial_no',
            'fields': [
                {'name': 'gst_number', 'label': 'GST Number', 'type': 'text', 'required': True},
                {'name': 'pan', 'label': 'PAN', 'type': 'text', 'required': True},
                {'name': 'business_code', 'label': 'Business', 'type': 'select', 'options': biz_opts, 'required': True},
                {'name': 'reg_date', 'label': 'Reg Date', 'type': 'date', 'required': True},
                {'name': 'valid_till', 'label': 'Valid Till', 'type': 'date', 'required': True},
                {'name': 'address', 'label': 'Address', 'type': 'text', 'required': True},
                {'name': 'city', 'label': 'City', 'type': 'text', 'required': True},
                {'name': 'pin', 'label': 'PIN', 'type': 'text', 'required': True},
                {'name': 'country', 'label': 'Country', 'type': 'text', 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': STATUS, 'required': True},
            ]
        },
        'categories': {
            'title': 'Product Category', 'icon': 'bi-tags', 'model': 'ProductCategory', 'pk': 'id',
            'fields': [
                {'name': 'category', 'label': 'Category', 'type': 'text', 'required': True},
                {'name': 'sub_category', 'label': 'Sub Category', 'type': 'text', 'required': True},
                {'name': 'hsn', 'label': 'HSN Code', 'type': 'text', 'required': True},
                {'name': 'sgst', 'label': 'SGST %', 'type': 'number', 'required': True},
                {'name': 'cgst', 'label': 'CGST %', 'type': 'number', 'required': True},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'products': {
            'title': 'Product', 'icon': 'bi-box-seam', 'model': 'Product', 'pk': 'id',
            'fields': [
                {'name': 'product_name', 'label': 'Product Name', 'type': 'text', 'required': True},
                {'name': 'description', 'label': 'Description', 'type': 'textarea', 'required': True, 'full_width': True},
                {'name': 'product_category', 'label': 'Category', 'type': 'select', 'options': cat_opts, 'required': True},
                {'name': 'business_code', 'label': 'Business', 'type': 'select', 'options': biz_opts, 'required': False},
                {'name': 'quantity', 'label': 'Quantity', 'type': 'number', 'required': True},
                {'name': 'unit', 'label': 'Unit', 'type': 'text', 'required': True},
                {'name': 'mrp', 'label': 'MRP', 'type': 'number', 'required': True},
                {'name': 'selling_price', 'label': 'Selling Price', 'type': 'number', 'required': True},
                {'name': 'cost_price', 'label': 'Cost Price', 'type': 'number', 'required': False},
                {'name': 'stock', 'label': 'Stock', 'type': 'number', 'required': True},
                {'name': 'ship_cost', 'label': 'Ship Cost', 'type': 'number', 'required': False},
                {'name': 'source', 'label': 'Source', 'type': 'text', 'required': True},
                {'name': 'manufacturer', 'label': 'Manufacturer', 'type': 'text', 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': STATUS, 'required': True},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'orders': {
            'title': 'Order', 'icon': 'bi-cart3', 'model': 'Order', 'pk': 'order_id',
            'fields': [
                {'name': 'order_id', 'label': 'Order ID', 'type': 'text', 'required': True},
                {'name': 'customer_name', 'label': 'Customer Name', 'type': 'text', 'required': True},
                {'name': 'customer_email', 'label': 'Customer Email', 'type': 'email', 'required': True},
                {'name': 'customer_phone', 'label': 'Customer Phone', 'type': 'text', 'required': True},
                {'name': 'total_amount', 'label': 'Total Amount', 'type': 'number', 'required': True},
                {'name': 'delivery_charge', 'label': 'Delivery Charge', 'type': 'number', 'required': False},
                {'name': 'payment_method', 'label': 'Payment Method', 'type': 'select', 'options': PAY_MODE, 'required': True},
                {'name': 'payment_status', 'label': 'Payment Status', 'type': 'select', 'options': PAY_STATUS, 'required': True},
                {'name': 'order_status', 'label': 'Order Status', 'type': 'select', 'options': ORDER_STATUS, 'required': True},
                {'name': 'sold_by', 'label': 'Sold By', 'type': 'text', 'required': True},
                {'name': 'bill_name', 'label': 'Bill Name', 'type': 'text', 'required': True},
                {'name': 'bill_phone', 'label': 'Bill Phone', 'type': 'text', 'required': True},
                {'name': 'bill_address1', 'label': 'Bill Address', 'type': 'text', 'required': True},
                {'name': 'bill_city', 'label': 'Bill City', 'type': 'text', 'required': True},
                {'name': 'bill_state', 'label': 'Bill State', 'type': 'text', 'required': True},
                {'name': 'bill_pin', 'label': 'Bill PIN', 'type': 'text', 'required': True},
                {'name': 'ship_name', 'label': 'Ship Name', 'type': 'text', 'required': True},
                {'name': 'ship_phone', 'label': 'Ship Phone', 'type': 'text', 'required': True},
                {'name': 'ship_address1', 'label': 'Ship Address', 'type': 'text', 'required': True},
                {'name': 'ship_city', 'label': 'Ship City', 'type': 'text', 'required': True},
                {'name': 'ship_state', 'label': 'Ship State', 'type': 'text', 'required': True},
                {'name': 'ship_pin', 'label': 'Ship PIN', 'type': 'text', 'required': True},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'payments': {
            'title': 'Payment', 'icon': 'bi-credit-card', 'model': 'Payment', 'pk': 'id',
            'fields': [
                {'name': 'transaction_id', 'label': 'Transaction ID', 'type': 'text', 'required': True},
                {'name': 'reference_order', 'label': 'Order', 'type': 'select', 'options': order_opts, 'required': True},
                {'name': 'amount', 'label': 'Amount', 'type': 'number', 'required': True},
                {'name': 'payment_mode', 'label': 'Payment Mode', 'type': 'select', 'options': PAY_MODE, 'required': True},
                {'name': 'transaction_type', 'label': 'Transaction Type', 'type': 'select', 'options': TXN_TYPE, 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': [{'value': v, 'label': v} for v in ['Pending','Processing','Successful','Failed','Cancelled']], 'required': True},
                {'name': 'avs_wallet_id', 'label': 'Wallet ID', 'type': 'text', 'required': False},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'refunds': {
            'title': 'Refund', 'icon': 'bi-arrow-counterclockwise', 'model': 'Refund', 'pk': 'id',
            'fields': [
                {'name': 'reference_order', 'label': 'Order', 'type': 'select', 'options': order_opts, 'required': True},
                {'name': 'amount', 'label': 'Amount', 'type': 'number', 'required': True},
                {'name': 'payment_mode', 'label': 'Payment Mode', 'type': 'text', 'required': True},
                {'name': 'customer_status', 'label': 'Customer Status', 'type': 'text', 'required': True},
                {'name': 'seller_status', 'label': 'Seller Status', 'type': 'text', 'required': True},
                {'name': 'refund_status', 'label': 'Refund Status', 'type': 'select', 'options': REFUND_STATUS, 'required': True},
                {'name': 'cancellation_reason', 'label': 'Cancellation Reason', 'type': 'textarea', 'required': True, 'full_width': True},
                {'name': 'refund_reason', 'label': 'Refund Reason', 'type': 'textarea', 'required': False, 'full_width': True},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'wallets': {
            'title': 'Wallet', 'icon': 'bi-wallet2', 'model': 'Wallet', 'pk': 'wallet_id',
            'fields': [
                {'name': 'customer_name', 'label': 'Customer Name', 'type': 'text', 'required': True},
                {'name': 'customer_id', 'label': 'Customer ID', 'type': 'text', 'required': True},
                {'name': 'customer_mobile', 'label': 'Mobile', 'type': 'text', 'required': True},
                {'name': 'wallet_type', 'label': 'Wallet Type', 'type': 'select', 'options': WALLET_TYPE, 'required': True},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'wallet_transactions': {
            'title': 'Wallet Transaction', 'icon': 'bi-arrow-left-right', 'model': 'WalletTransaction', 'pk': 'id',
            'fields': [
                {'name': 'transaction_id', 'label': 'Transaction ID', 'type': 'text', 'required': True},
                {'name': 'avs_customer_name', 'label': 'Customer Name', 'type': 'text', 'required': True},
                {'name': 'avs_customer_id', 'label': 'Customer ID', 'type': 'text', 'required': True},
                {'name': 'avs_customer_mobile', 'label': 'Mobile', 'type': 'text', 'required': True},
                {'name': 'transaction_type', 'label': 'Type', 'type': 'select', 'options': TXN_TYPE, 'required': True},
                {'name': 'amount', 'label': 'Amount', 'type': 'number', 'required': True},
                {'name': 'reference_order', 'label': 'Order (optional)', 'type': 'select', 'options': [{'value': '', 'label': '— None —'}] + order_opts, 'required': False},
                {'name': 'transaction_date', 'label': 'Transaction Date', 'type': 'datetime-local', 'required': True},
                {'name': 'transaction_for', 'label': 'Transaction For', 'type': 'text', 'required': False},
                {'name': 'transaction_by', 'label': 'Transaction By', 'type': 'text', 'required': True},
            ]
        },
        'customers': {
            'title': 'Customer', 'icon': 'bi-people', 'model': 'Customer', 'pk': 'id',
            'fields': [
                {'name': 'first_name', 'label': 'First Name', 'type': 'text', 'required': True},
                {'name': 'middle_name', 'label': 'Middle Name', 'type': 'text', 'required': False},
                {'name': 'last_name', 'label': 'Last Name', 'type': 'text', 'required': True},
                {'name': 'email', 'label': 'Email', 'type': 'email', 'required': True},
                {'name': 'phone', 'label': 'Phone', 'type': 'text', 'required': True},
                {'name': 'username', 'label': 'Username', 'type': 'text', 'required': True},
                {'name': 'password', 'label': 'Password', 'type': 'text', 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'checkbox', 'required': False},
            ]
        },
        'units': {
            'title': 'Unit of Measurement', 'icon': 'bi-rulers', 'model': 'UnitOfMeasurement', 'pk': 'id',
            'fields': [
                {'name': 'name', 'label': 'Name', 'type': 'text', 'required': True},
                {'name': 'abbreviation', 'label': 'Abbreviation', 'type': 'text', 'required': True},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'delivery_settings': {
            'title': 'Delivery Settings', 'icon': 'bi-gear', 'model': 'DeliverySettings', 'pk': 'id',
            'fields': [
                {'name': 'business_code', 'label': 'Business', 'type': 'select', 'options': biz_opts, 'required': True},
                {'name': 'store_address', 'label': 'Store Address', 'type': 'text', 'required': False},
                {'name': 'store_area', 'label': 'Store Area', 'type': 'text', 'required': False},
                {'name': 'store_city', 'label': 'Store City', 'type': 'text', 'required': False},
                {'name': 'store_pin', 'label': 'Store PIN', 'type': 'text', 'required': False},
                {'name': 'delivery_free', 'label': 'Delivery Free', 'type': 'checkbox', 'required': False},
                {'name': 'ship_free', 'label': 'Ship Free', 'type': 'checkbox', 'required': False},
                {'name': 'min_amount_free_delivery', 'label': 'Min Amount for Free Delivery', 'type': 'number', 'required': False},
                {'name': 'max_distance_km', 'label': 'Max Distance (km)', 'type': 'number', 'required': False},
            ]
        },
        'delivery_zones': {
            'title': 'Delivery Zone', 'icon': 'bi-map', 'model': 'DeliveryZone', 'pk': 'id',
            'fields': [
                {'name': 'business_code', 'label': 'Business', 'type': 'select', 'options': biz_opts, 'required': True},
                {'name': 'zone_name', 'label': 'Zone Name', 'type': 'text', 'required': True},
                {'name': 'pincode_to', 'label': 'Pincode', 'type': 'text', 'required': True},
                {'name': 'distance_range_km', 'label': 'Distance (km)', 'type': 'number', 'required': False},
                {'name': 'base_charge', 'label': 'Base Charge', 'type': 'number', 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': STATUS, 'required': True},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'management_users': {
            'title': 'Management User', 'icon': 'bi-person-lock', 'model': 'ManagementUser', 'pk': 'id',
            'fields': [
                {'name': 'first_name', 'label': 'First Name', 'type': 'text', 'required': True},
                {'name': 'last_name', 'label': 'Last Name', 'type': 'text', 'required': True},
                {'name': 'email', 'label': 'Email', 'type': 'email', 'required': True},
                {'name': 'phone', 'label': 'Phone', 'type': 'text', 'required': True},
                {'name': 'username', 'label': 'Username', 'type': 'text', 'required': True},
                {'name': 'password', 'label': 'Password', 'type': 'text', 'required': True},
                {'name': 'role', 'label': 'Role', 'type': 'select', 'options': ROLE, 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': STATUS, 'required': True},
            ]
        },
        'wallet_api_config': {
            'title': 'Wallet API Config', 'icon': 'bi-sliders', 'model': 'WalletAPIConfig', 'pk': 'id',
            'fields': [
                {'name': 'config_name', 'label': 'Config Name', 'type': 'text', 'required': True},
                {'name': 'source_name', 'label': 'Source System Name', 'type': 'text', 'required': True},
                {'name': 'endpoint_url', 'label': 'Endpoint URL', 'type': 'text', 'required': False},
                {'name': 'http_method', 'label': 'HTTP Method', 'type': 'select', 'options': [{'value': 'POST', 'label': 'POST'}, {'value': 'GET', 'label': 'GET'}], 'required': True},
                {'name': 'auth_type', 'label': 'Auth Type', 'type': 'select', 'required': True, 'options': [
                    {'value': 'api_key_header', 'label': 'API Key (Header)'},
                    {'value': 'api_key_param', 'label': 'API Key (Query Param)'},
                    {'value': 'bearer_token', 'label': 'Bearer Token'},
                    {'value': 'basic_auth', 'label': 'Basic Auth'},
                    {'value': 'none', 'label': 'No Auth'},
                ]},
                {'name': 'auth_key_name', 'label': 'Auth Key Name (e.g. X-API-Key)', 'type': 'text', 'required': False},
                {'name': 'auth_key_value', 'label': 'Auth Key Value / Token', 'type': 'text', 'required': False},
                {'name': 'extra_headers', 'label': 'Extra Headers (JSON)', 'type': 'textarea', 'required': False, 'full_width': True},
                {'name': 'request_body_template', 'label': 'Request Body Template (JSON)', 'type': 'textarea', 'required': False, 'full_width': True},
                {'name': 'resp_data_path', 'label': 'Response Data Path (e.g. data.transactions)', 'type': 'text', 'required': False, 'full_width': True},
                {'name': 'resp_transaction_id', 'label': 'Response Field → Transaction ID', 'type': 'text', 'required': True},
                {'name': 'resp_customer_id', 'label': 'Response Field → Customer ID', 'type': 'text', 'required': True},
                {'name': 'resp_customer_name', 'label': 'Response Field → Customer Name', 'type': 'text', 'required': True},
                {'name': 'resp_mobile', 'label': 'Response Field → Mobile', 'type': 'text', 'required': True},
                {'name': 'resp_amount', 'label': 'Response Field → Amount', 'type': 'text', 'required': True},
                {'name': 'resp_type', 'label': 'Response Field → Type (Credit/Debit)', 'type': 'text', 'required': True},
                {'name': 'resp_transaction_date', 'label': 'Response Field → Transaction Date', 'type': 'text', 'required': True},
                {'name': 'resp_transaction_for', 'label': 'Response Field → Transaction For', 'type': 'text', 'required': False},
                {'name': 'resp_transaction_by', 'label': 'Response Field → Transaction By', 'type': 'text', 'required': False},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': STATUS, 'required': True},
                {'name': 'created_by', 'label': 'Created By', 'type': 'text', 'required': True},
            ]
        },
        'staff_users': {
            'title': 'Staff User', 'icon': 'bi-person-circle', 'model': 'StaffUser', 'pk': 'id',
            'fields': [
                {'name': 'first_name', 'label': 'First Name', 'type': 'text', 'required': True},
                {'name': 'middle_name', 'label': 'Middle Name', 'type': 'text', 'required': False},
                {'name': 'last_name', 'label': 'Last Name', 'type': 'text', 'required': True},
                {'name': 'email', 'label': 'Email', 'type': 'email', 'required': True},
                {'name': 'phone', 'label': 'Phone', 'type': 'text', 'required': True},
                {'name': 'password', 'label': 'Password (leave blank to keep)', 'type': 'text', 'required': False},
                {'name': 'status', 'label': 'Active', 'type': 'checkbox', 'required': False},
            ]
        },
        'staff': {
            'title': 'Staff', 'icon': 'bi-person-badge', 'model': 'Staff', 'pk': 'staff_id',
            'fields': [
                {'name': 'staff_id', 'label': 'Staff ID', 'type': 'text', 'required': True},
                {'name': 'username', 'label': 'Staff User', 'type': 'select', 'options': staff_user_opts, 'required': True},
                {'name': 'business_code', 'label': 'Business', 'type': 'select', 'options': biz_opts, 'required': True},
                {'name': 'role', 'label': 'Role', 'type': 'select', 'options': [{'value': 'Admin', 'label': 'Admin'}, {'value': 'Staff', 'label': 'Staff'}], 'required': True},
                {'name': 'phone', 'label': 'Phone', 'type': 'text', 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': STATUS, 'required': True},
            ]
        },
    }
    return configs.get(table)


def _get_model(table):
    from management.models import (
        BusinessDetail, GSTDetail, ProductCategory, Product,
        Order, Payment, UnitOfMeasurement, Wallet, WalletTransaction,
        Refund, DeliverySettings, DeliveryZone, ManagementUser, WalletAPIConfig
    )
    from customer.models import Customer
    from seller.models import Staff, StaffUser
    return {
        'business': BusinessDetail, 'gst': GSTDetail, 'categories': ProductCategory,
        'products': Product, 'orders': Order, 'payments': Payment,
        'units': UnitOfMeasurement, 'wallets': Wallet, 'wallet_transactions': WalletTransaction,
        'refunds': Refund, 'delivery_settings': DeliverySettings, 'delivery_zones': DeliveryZone,
        'customers': Customer, 'staff_users': StaffUser, 'staff': Staff,
        'management_users': ManagementUser, 'wallet_api_config': WalletAPIConfig,
    }.get(table)


def _gen_staff_username(first_name, last_name):
    from seller.models import StaffUser
    base = (last_name[:2] + first_name[:4]).upper()
    seq = 1
    while StaffUser.objects.filter(username=f'{base}{seq:02d}').exists():
        seq += 1
    return f'{base}{seq:02d}'


def mgmt_add(request, table):
    if not _mgmt_auth(request):
        return redirect('mgmt_login')
    config = _get_form_config(table)
    Model = _get_model(table)
    if not config or not Model:
        return redirect('mgmt_dashboard')

    error = None
    if request.method == 'POST':
        try:
            if table == 'staff_users':
                from seller.models import StaffUser
                p = request.POST
                if StaffUser.objects.filter(email=p['email']).exists():
                    raise Exception('Email already exists')
                username = _gen_staff_username(p['first_name'], p['last_name'])
                StaffUser.objects.create(
                    first_name=p['first_name'], middle_name=p.get('middle_name') or None,
                    last_name=p['last_name'], email=p['email'], phone=p['phone'],
                    username=username, password=p['password'],
                    status='status' in request.POST,
                )
                return redirect('mgmt_table', table=table)
            if table == 'staff':
                from seller.models import StaffUser, Staff as StaffModel
                p = request.POST
                if StaffModel.objects.filter(staff_id=p['staff_id']).exists():
                    raise Exception('Staff ID already exists')
                staff_user = StaffUser.objects.get(username=p['username'])
                StaffModel.objects.create(
                    staff_id=p['staff_id'], username=staff_user,
                    business_code_id=p['business_code'], role=p['role'],
                    phone=p['phone'], status=p['status'],
                    created_by=request.session.get('mgmt_username', 'management'),
                )
                return redirect('mgmt_table', table=table)
            data = {}
            for field in config['fields']:
                val = request.POST.get(field['name'], '')
                if field['type'] == 'checkbox':
                    val = field['name'] in request.POST
                elif field['name'] in ('product_category', 'business_code', 'reference_order') and val == '':
                    val = None
                data[field['name']] = val if val != '' else None if not field.get('required') else val
            for fk in ('product_category', 'business_code', 'reference_order'):
                if fk in data:
                    data[f'{fk}_id'] = data.pop(fk)
            obj = Model(**{k: v for k, v in data.items() if v is not None or not config.get('required')})
            obj.save()
            return redirect('mgmt_table', table=table)
        except Exception as e:
            error = str(e)

    fields = [dict(f, current='') for f in config['fields']]
    return render(request, 'management/form.html', {
        'table': table, 'title': config['title'], 'icon': config['icon'],
        'action': 'Add', 'fields': fields, 'error': error,
    })


def mgmt_edit(request, table, pk):
    if not _mgmt_auth(request):
        return redirect('mgmt_login')
    config = _get_form_config(table)
    Model = _get_model(table)
    if not config or not Model:
        return redirect('mgmt_dashboard')

    pk_field = config['pk']
    try:
        obj = Model.objects.get(**{pk_field: pk})
    except Model.DoesNotExist:
        return redirect('mgmt_table', table=table)

    error = None
    if request.method == 'POST':
        try:
            if table == 'staff_users':
                from seller.models import StaffUser
                p = request.POST
                if StaffUser.objects.filter(email=p['email']).exclude(pk=obj.pk).exists():
                    raise Exception('Email already exists')
                obj.first_name = p['first_name']
                obj.middle_name = p.get('middle_name') or None
                obj.last_name = p['last_name']
                obj.email = p['email']
                obj.phone = p['phone']
                if p.get('password'):
                    obj.password = p['password']
                obj.status = 'status' in request.POST
                obj.save()
                return redirect('mgmt_table', table=table)
            for field in config['fields']:
                fname = field['name']
                val = request.POST.get(fname, '')
                if field['type'] == 'checkbox':
                    val = fname in request.POST
                elif fname in ('product_category', 'business_code', 'reference_order'):
                    setattr(obj, f'{fname}_id', val if val else None)
                    continue
                setattr(obj, fname, val)
            obj.save()
            return redirect('mgmt_table', table=table)
        except Exception as e:
            error = str(e)

    # Build fields with current values
    fields = []
    for f in config['fields']:
        fname = f['name']
        if fname in ('product_category', 'business_code', 'reference_order'):
            current = getattr(obj, f'{fname}_id', '')
        else:
            current = getattr(obj, fname, '')
        fields.append(dict(f, current=current if current is not None else ''))

    return render(request, 'management/form.html', {
        'table': table, 'title': config['title'], 'icon': config['icon'],
        'action': 'Edit', 'fields': fields, 'error': error,
    })


def mgmt_delete(request, table, pk):
    if not _mgmt_auth(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    config = _get_form_config(table)
    Model = _get_model(table)
    if not config or not Model:
        return JsonResponse({'success': False, 'error': 'Invalid table'})
    try:
        obj = Model.objects.get(**{config['pk']: pk})
        obj.delete()
        return JsonResponse({'success': True})
    except Model.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Record not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def mgmt_wallet_import(request):
    if not _mgmt_auth(request):
        return redirect('mgmt_login')

    from management.models import Wallet, WalletTransaction

    # Internal WalletTransaction fields available for mapping
    INTERNAL_FIELDS = [
        ('transaction_id',       'Transaction ID (required)'),
        ('avs_customer_id',      'Customer ID (required)'),
        ('avs_customer_name',    'Customer Name (required)'),
        ('avs_customer_mobile',  'Mobile'),
        ('transaction_type',     'Type — Credit/Debit/Refund (required)'),
        ('amount',               'Amount (required)'),
        ('transaction_date',     'Transaction Date (required)'),
        ('transaction_for',      'Transaction For'),
        ('transaction_by',       'Transaction By'),
    ]

    file_headers = request.session.get('import_headers', [])
    result = None
    step = 'upload'  # upload | map | done

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Step 1: Upload file, detect headers ──────────────────────────────
        if action == 'upload':
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                result = {'error': 'Please select a file.'}
            else:
                try:
                    import pandas as pd, io
                    content = uploaded_file.read()
                    fname = uploaded_file.name.lower()
                    if fname.endswith('.csv'):
                        df = pd.read_csv(io.BytesIO(content), nrows=0)
                    elif fname.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(io.BytesIO(content), nrows=0)
                    else:
                        result = {'error': 'Only CSV or Excel files supported.'}
                        return render(request, 'management/wallet_import.html', {
                            'step': 'upload', 'result': result, 'active': 'wallet_import', 'internal_fields': INTERNAL_FIELDS
                        })
                    file_headers = list(df.columns)
                    # Store file content and headers in session
                    import base64
                    request.session['import_file'] = base64.b64encode(content).decode()
                    request.session['import_ext'] = 'csv' if fname.endswith('.csv') else 'xlsx'
                    request.session['import_headers'] = file_headers
                    step = 'map'
                except Exception as e:
                    result = {'error': str(e)}

        # ── Step 2: Apply mapping and import ─────────────────────────────────
        elif action == 'import':
            try:
                import pandas as pd, io, base64
                content = base64.b64decode(request.session.get('import_file', ''))
                ext = request.session.get('import_ext', 'csv')
                file_headers = request.session.get('import_headers', [])

                if ext == 'csv':
                    df = pd.read_csv(io.BytesIO(content))
                else:
                    df = pd.read_excel(io.BytesIO(content))

                # Build mapping from POST: internal_field -> file_column
                mapping = {}
                for internal, _ in INTERNAL_FIELDS:
                    col = request.POST.get(f'map_{internal}', '').strip()
                    if col:
                        mapping[internal] = col

                required = ['transaction_id', 'avs_customer_id', 'avs_customer_name', 'amount', 'transaction_type', 'transaction_date']
                missing = [r for r in required if r not in mapping]
                if missing:
                    result = {'error': f'Please map required fields: {", ".join(missing)}'}
                    step = 'map'
                else:
                    success, skipped, errors = 0, 0, []
                    mgmt_user = request.session.get('mgmt_name', 'Management')

                    for i, row in df.iterrows():
                        try:
                            txn_id   = str(row[mapping['transaction_id']]).strip()
                            cust_id  = str(row[mapping['avs_customer_id']]).strip()
                            cust_name = str(row[mapping['avs_customer_name']]).strip()
                            txn_type = str(row[mapping['transaction_type']]).strip()
                            amount   = Decimal(str(row[mapping['amount']]))
                            txn_date_raw = str(row[mapping['transaction_date']]).strip()

                            if WalletTransaction.objects.filter(transaction_id=txn_id).exists():
                                skipped += 1
                                continue

                            if txn_type not in ('Credit', 'Debit', 'Refund'):
                                errors.append(f'Row {i+2}: Invalid type "{txn_type}"')
                                continue

                            txn_date = parse_datetime(txn_date_raw) or timezone.now()
                            mobile   = str(row.get(mapping.get('avs_customer_mobile', ''), '')).strip() if mapping.get('avs_customer_mobile') else ''
                            txn_for  = str(row[mapping['transaction_for']]).strip() if mapping.get('transaction_for') else ''
                            txn_by   = str(row[mapping['transaction_by']]).strip() if mapping.get('transaction_by') else mgmt_user

                            wallet = Wallet.objects.filter(customer_id=cust_id, wallet_type='AVS').first()
                            if not wallet:
                                wallet = Wallet.objects.create(
                                    wallet_type='AVS', customer_name=cust_name,
                                    customer_id=cust_id, customer_mobile=mobile, created_by=mgmt_user,
                                )

                            WalletTransaction.objects.create(
                                transaction_id=txn_id,
                                avs_customer_name=cust_name or wallet.customer_name,
                                avs_customer_id=cust_id,
                                avs_customer_mobile=mobile or wallet.customer_mobile,
                                transaction_type=txn_type,
                                amount=amount,
                                reference_order=None,
                                transaction_date=txn_date,
                                transaction_for=txn_for,
                                transaction_by=txn_by,
                            )
                            success += 1
                        except Exception as e:
                            errors.append(f'Row {i+2}: {str(e)}')

                    # Clear session
                    for k in ('import_file', 'import_ext', 'import_headers'):
                        request.session.pop(k, None)

                    result = {'success': success, 'skipped': skipped, 'errors': errors[:20]}
                    step = 'done'

            except Exception as e:
                result = {'error': str(e)}
                step = 'map'

    elif file_headers:
        step = 'map'

    return render(request, 'management/wallet_import.html', {
        'step': step,
        'file_headers': file_headers,
        'internal_fields': INTERNAL_FIELDS,
        'result': result,
        'active': 'wallet_import',
    })


# ── Existing wallet API ──────────────────────────────────────────────────────
@csrf_exempt
@require_POST
def wallet_transaction_api(request):
    if not _api_auth(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    transaction_id    = data.get('transaction_id', '').strip()
    avs_customer_id   = data.get('avs_customer_id', '').strip()
    avs_customer_name = data.get('avs_customer_name', '').strip()
    mobile            = data.get('mobile', '').strip()
    txn_type          = data.get('type', '').strip()
    transaction_for   = data.get('transaction_for', '')
    transaction_by    = data.get('transaction_by', 'API')
    raw_date          = data.get('transaction_date', '')

    if not all([transaction_id, avs_customer_id, txn_type]):
        return JsonResponse({'error': 'transaction_id, avs_customer_id and type are required'}, status=400)

    if txn_type not in ('Credit', 'Debit'):
        return JsonResponse({'error': 'type must be Credit or Debit'}, status=400)

    try:
        amount = Decimal(str(data.get('amount', '')))
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        return JsonResponse({'error': 'Invalid amount'}, status=400)

    transaction_date = parse_datetime(raw_date) if raw_date else timezone.now()
    if transaction_date is None:
        transaction_date = timezone.now()

    from management.models import Wallet, WalletTransaction

    wallet = Wallet.objects.filter(customer_id=avs_customer_id, wallet_type='AVS').first()
    if not wallet:
        wallet = Wallet.objects.create(
            wallet_type='AVS',
            customer_name=avs_customer_name,
            customer_id=avs_customer_id,
            customer_mobile=mobile,
            created_by='API',
        )

    wallet.modified_by = transaction_by
    wallet.save()

    WalletTransaction.objects.create(
        transaction_id=transaction_id,
        avs_customer_name=avs_customer_name or wallet.customer_name,
        avs_customer_id=avs_customer_id,
        avs_customer_mobile=mobile or wallet.customer_mobile,
        transaction_type=txn_type,
        amount=amount,
        reference_order=None,
        transaction_date=transaction_date,
        transaction_for=transaction_for,
        transaction_by=transaction_by,
    )

    return JsonResponse({
        'success': True,
        'wallet_id': wallet.wallet_id,
        'new_balance': str(wallet.wallet_amount),
    })
