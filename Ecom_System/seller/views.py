from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from management.models import Product, ProductCategory, Order, BusinessDetail, ProductImage
from django.db import models
from .models import Staff, StaffUser
from django.contrib import messages

def staff_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        business_code = request.POST.get('business_code')
        
        try:
            user = StaffUser.objects.get(username=username)
            if not business_code:
                return render(request, 'seller/staff_login.html', {'error': 'Business code is required for staff login'})
            
            staff = Staff.objects.get(username=user, business_code=business_code)
            
            # Check if staff status is Active
            if staff.status != 'Active':
                return render(request, 'seller/staff_login.html', {'error': 'Your account is not active. Please contact administrator.'})
            
            request.session['user_id'] = username
            request.session['is_logged_in'] = True
            request.session['user_type'] = 'staff'
            request.session['business_code'] = business_code
            return redirect('seller_dashboard')
        except (StaffUser.DoesNotExist, Staff.DoesNotExist):
            return render(request, 'seller/staff_login.html', {'error': 'Invalid credentials or business code'})
    
    return render(request, 'seller/staff_login.html')


def staff_logout(request):
    request.session.flush()
    return redirect('staff_login')


def seller_profile_view(request, username):
    if not request.session.get('is_logged_in'):
        return redirect('staff_login')
    
    session_username = request.session.get('user_id')
    if session_username != username:
        return redirect('staff_login')
    
    user = StaffUser.objects.get(username=username)
    profile = user.profile
    business_code = request.session.get('business_code')
    staff = Staff.objects.get(username=user, business_code=business_code)
    is_admin = staff.staff_role in ['Seller-Admin', 'Shop-Admin', 'Admin']
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_pic':
            if request.FILES.get('profile_picture'):
                profile.profile_pic = request.FILES['profile_picture']
                profile.save()
            return render(request, 'seller/profile.html', {'user': user, 'profile': profile, 'staff': staff, 'is_admin': is_admin, 'success': 'Profile picture updated successfully'})

        if not is_admin:
            return render(request, 'seller/profile.html', {'user': user, 'profile': profile, 'staff': staff, 'is_admin': is_admin, 'error': 'Only admins can edit profile information'})

        # Admin-only: update personal info
        user.first_name = request.POST.get('first_name')
        user.middle_name = request.POST.get('middle_name')
        user.last_name = request.POST.get('last_name')
        user.save()

        profile.address1 = request.POST.get('address1')
        profile.address2 = request.POST.get('address2')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.pin = request.POST.get('pin')
        profile.country = request.POST.get('country')
        profile.phone1 = request.POST.get('phone1')
        profile.phone2 = request.POST.get('phone2')
        profile.dob = request.POST.get('dob') or None
        profile.aadhaar_number = request.POST.get('aadhaar_number')
        profile.pan_number = request.POST.get('pan_number', '').upper()
        if request.FILES.get('aadhaar_attachment'):
            profile.aadhaar_attachment = request.FILES['aadhaar_attachment']
        if request.FILES.get('pan_attachment'):
            profile.pan_attachment = request.FILES['pan_attachment']
        profile.save()

        return render(request, 'seller/profile.html', {'user': user, 'profile': profile, 'staff': staff, 'is_admin': is_admin, 'success': 'Profile updated successfully'})
    
    return render(request, 'seller/profile.html', {'user': user, 'profile': profile, 'staff': staff, 'is_admin': is_admin})


def seller_dashboard(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    from management.models import Payment
    from seller.models import StaffPrivileges
    from django.core.paginator import Paginator
    from django.db.models import Sum
    
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    
    # Get current staff and privileges
    current_user = StaffUser.objects.get(username=username)
    current_staff = Staff.objects.get(username=current_user, business_code=business_code)
    privileges = StaffPrivileges.objects.filter(staff=current_staff).first()
    
    # Check if admin role (has all privileges)
    is_admin = current_staff.staff_role in ['Seller-Admin', 'Shop-Admin']
    
    products = Product.objects.filter(business_code=business_code)
    
    # Get orders based on view type
    view_type = request.GET.get('view', 'active')
    sort_field = request.GET.get('sort', 'created_at')
    sort_order = request.GET.get('order', 'desc')
    period_days = int(request.GET.get('period', 7))
    
    # Map frontend field names to model fields
    field_map = {
        'order_id': 'order_id',
        'customer_name': 'customer_name',
        'total_amount': 'total_amount',
        'payment_status': 'payment_status',
        'payment_method': 'payment_method',
        'created_at': 'created_at',
        'status_at': 'created_at',
        'status_by': 'placed_by'
    }
    
    order_by = field_map.get(sort_field, 'created_at')
    if sort_order == 'desc':
        order_by = '-' + order_by
    
    if view_type == 'completed':
        from django.utils import timezone
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=period_days)
        all_orders = Order.objects.filter(
            sold_by=business_code,
            order_status__in=['Delivered', 'Cancelled']
        ).filter(
            models.Q(delivered_at__gte=cutoff_date) | models.Q(cancelled_at__gte=cutoff_date)
        ).order_by(order_by)
    else:
        all_orders = Order.objects.filter(sold_by=business_code).exclude(order_status__in=['Delivered', 'Cancelled']).order_by(order_by)
    
    paginator = Paginator(all_orders, 20)
    page_number = request.GET.get('page', 1)
    orders = paginator.get_page(page_number)
    
    staff_count = Staff.objects.filter(business_code=business_code).count()
    staff_list = Staff.objects.filter(business_code=business_code)
    payments = Payment.objects.filter(reference_order__sold_by=business_code).order_by('-created_at')
    cod_orders = Order.objects.filter(sold_by=business_code, payment_method__in=['COD']).order_by('-created_at')
    
    from management.models import Refund
    refunds = Refund.objects.filter(reference_order__sold_by=business_code, refund_status='Pending').order_by('-created_at')
    refund_history = Refund.objects.filter(reference_order__sold_by=business_code).exclude(refund_status='Pending').order_by('-modified_at')
    
    # Dashboard overview stats
    all_orders = Order.objects.filter(sold_by=business_code)
    active_orders_count = all_orders.exclude(order_status__in=['Delivered', 'Cancelled']).count()
    completed_orders_count = all_orders.filter(order_status='Delivered').count()
    cancelled_orders_count = all_orders.filter(order_status='Cancelled').count()
    total_revenue = all_orders.filter(order_status='Delivered', payment_status='Successful').aggregate(total=Sum('total_amount'))['total'] or 0
    pending_payments_count = payments.filter(status='Pending').count()
    pending_refunds_count = refunds.count()
    active_products_count = products.filter(status='Active').count()
    low_stock_count = products.filter(status='Active', stock__lt=5).count()
    out_of_stock_count = products.filter(status='Active', stock=0).count()
    active_staff_count = Staff.objects.filter(business_code=business_code, status='Active').count()

    # Report stats
    from django.db.models import Count, Avg
    total_orders_all = Order.objects.filter(sold_by=business_code)
    report_revenue_total = total_orders_all.filter(order_status='Delivered', payment_status='Successful').aggregate(total=models.Sum('total_amount'))['total'] or 0
    report_avg_order = total_orders_all.filter(order_status='Delivered').aggregate(avg=Avg('total_amount'))['avg'] or 0
    report_orders_by_status = list(total_orders_all.values('order_status').annotate(c=Count('order_id')).order_by('order_status'))
    report_orders_by_payment = list(total_orders_all.values('payment_method').annotate(c=Count('order_id')).order_by('payment_method'))
    report_top_products = list(
        Product.objects.filter(business_code=business_code, status='Active').order_by('stock')[:5].values('product_name', 'stock', 'selling_price')
    )
    report_inactive_products = products.filter(status='Inactive').count()
    report_total_stock_value = products.filter(status='Active').aggregate(v=models.Sum(models.F('stock') * models.F('selling_price')))['v'] or 0
    report_staff_by_role = list(Staff.objects.filter(business_code=business_code).values('role').annotate(c=Count('staff_id')))
    report_refund_total = Refund.objects.filter(reference_order__sold_by=business_code, refund_status='Refunded').aggregate(total=models.Sum('amount'))['total'] or 0
    report_refund_count = Refund.objects.filter(reference_order__sold_by=business_code).count()
    
    return render(request, 'seller/seller_dashboard.html', {
        'products': products,
        'orders': orders,
        'staff_count': staff_count,
        'staff_list': staff_list,
        'payments': payments,
        'cod_orders': cod_orders,
        'refunds': refunds,
        'refund_history': refund_history,
        'business_code': business_code,
        'privileges': privileges,
        'is_admin': is_admin,
        'view_type': view_type,
        'total_count': paginator.count,
        'user': current_user,
        'active_orders_count': active_orders_count,
        'completed_orders_count': completed_orders_count,
        'cancelled_orders_count': cancelled_orders_count,
        'total_revenue': total_revenue,
        'pending_payments_count': pending_payments_count,
        'pending_refunds_count': pending_refunds_count,
        'active_products_count': active_products_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'active_staff_count': active_staff_count,
        'report_revenue_total': report_revenue_total,
        'report_avg_order': report_avg_order,
        'report_orders_by_status': report_orders_by_status,
        'report_orders_by_payment': report_orders_by_payment,
        'report_top_products': report_top_products,
        'report_inactive_products': report_inactive_products,
        'report_total_stock_value': report_total_stock_value,
        'report_staff_by_role': report_staff_by_role,
        'report_refund_total': report_refund_total,
        'report_refund_count': report_refund_count,
    })

def add_product(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    if request.method == 'POST':
        business_code = request.session.get('business_code')
        business = BusinessDetail.objects.get(code=business_code)
        username = request.session.get('user_id')
        user = StaffUser.objects.get(username=username)
        
        # Check if bulk upload
        if request.FILES.get('bulk_file'):
            import pandas as pd
            file = request.FILES['bulk_file']
            
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                success_count = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        category = ProductCategory.objects.filter(category=row['category'], sub_category=row['sub_category']).first()
                        if not category:
                            errors.append(f"Row {index+2}: Category not found")
                            continue
                        
                        Product.objects.create(
                            product_name=row['product_name'],
                            description=row.get('description', ''),
                            product_category=category,
                            quantity=row['quantity'],
                            unit=row['unit'],
                            mrp=row['mrp'],
                            selling_price=row['selling_price'],
                            stock=row['stock'],
                            source=row.get('source', ''),
                            manufacturer=row.get('manufacturer', ''),
                            business_code_id=business_code,
                            created_by=f"{user.first_name} {user.last_name}",
                            added_by=business.business_name
                        )
                        success_count += 1
                    except Exception as e:
                        errors.append(f"Row {index+2}: {str(e)}")
                
                if errors:
                    return render(request, 'seller/add_product.html', {
                        'categories': ProductCategory.objects.all(),
                        'success': f'{success_count} products added successfully',
                        'errors': errors
                    })
                return redirect('/seller/?tab=products#products')
            except Exception as e:
                return render(request, 'seller/add_product.html', {
                    'categories': ProductCategory.objects.all(),
                    'error': f'Error reading file: {str(e)}'
                })
        
        # Single product add
        category_id = request.POST.get('category')
        product = Product.objects.create(
            product_name=request.POST.get('product_name'),
            description=request.POST.get('description'),
            product_category_id=category_id,
            quantity=request.POST.get('quantity'),
            unit=request.POST.get('unit'),
            mrp=request.POST.get('mrp'),
            selling_price=request.POST.get('selling_price'),
            stock=request.POST.get('stock'),
            source=request.POST.get('source'),
            manufacturer=request.POST.get('manufacturer'),
            business_code_id=business_code,
            created_by=f"{user.first_name} {user.last_name}",
            added_by=business.business_name
        )
        
        images = request.FILES.getlist('images')
        for idx, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(idx == 0)
            )
        
        return redirect('/seller/?tab=products#products')
    
    categories = ProductCategory.objects.all()
    username = request.session.get('user_id')
    current_user = StaffUser.objects.get(username=username)
    return render(request, 'seller/add_product.html', {'categories': categories, 'user': current_user})

def edit_product(request, product_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    product = Product.objects.get(id=product_id)
    
    if request.method == 'POST':
        from django.utils import timezone
        username = request.session.get('user_id')
        user = StaffUser.objects.get(username=username)
        modifier_name = f"{user.first_name} {user.last_name}"
        
        product.product_name = request.POST.get('product_name')
        product.description = request.POST.get('description')
        product.product_category_id = request.POST.get('category')
        product.quantity = request.POST.get('quantity')
        product.unit = request.POST.get('unit')
        product.mrp = request.POST.get('mrp')
        product.selling_price = request.POST.get('selling_price')
        product.stock = request.POST.get('stock')
        product.source = request.POST.get('source')
        product.manufacturer = request.POST.get('manufacturer')
        product.status = request.POST.get('status')
        product.modified_by = modifier_name
        product.modified_at = timezone.now()
        product.save()
        
        images = request.FILES.getlist('images')
        for idx, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(idx == 0 and not product.images.exists())
            )
        
        return redirect('view_product', product_id=product_id)
    
    categories = ProductCategory.objects.all()
    username = request.session.get('user_id')
    current_user = StaffUser.objects.get(username=username)
    return render(request, 'seller/edit_product.html', {'product': product, 'categories': categories, 'user': current_user})

def view_product(request, product_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    product = Product.objects.get(id=product_id)
    username = request.session.get('user_id')
    current_user = StaffUser.objects.get(username=username)
    return render(request, 'seller/view_product.html', {'product': product, 'user': current_user})


def add_stock(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    if request.method == 'POST':
        from django.http import JsonResponse
        product_id = request.POST.get('product_id')
        qty = request.POST.get('quantity')
        try:
            product = Product.objects.get(id=product_id)
            product.stock += int(qty)
            user = StaffUser.objects.get(username=request.session.get('user_id'))
            product.modified_by = f"{user.first_name} {user.last_name}"
            from django.utils import timezone
            product.modified_at = timezone.now()
            product.save()
            return JsonResponse({'success': True, 'new_stock': product.stock, 'product_name': product.product_name})
        except (Product.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def update_order_status(request, order_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    if request.method == 'POST':
        import json
        from django.utils import timezone
        
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            comments = data.get('comments', '')
            
            username = request.session.get('user_id')
            user = StaffUser.objects.get(username=username)
            modifier_name = f"{user.first_name} {user.last_name}"
            
            order = Order.objects.get(order_id=order_id)
            order.order_status = new_status
            order.modified_by = modifier_name
            order.modified_at = timezone.now()
            order.modified_comments = comments

            if new_status == 'Confirmed':
                order.confirmed_at = timezone.now()
                order.confirmed_by = modifier_name
                order.confirmed_comments = comments
            elif new_status == 'Processing':
                order.processing_at = timezone.now()
                order.processing_by = modifier_name
                order.processing_comments = comments
            elif new_status == 'Shipped':
                order.shipped_at = timezone.now()
                order.shipped_by = modifier_name
                order.shipped_comments = comments
                if not order.invoice_no:
                    from django.db.models import Max
                    last_invoice = Order.objects.filter(sold_by=order.sold_by).aggregate(Max('invoice_no'))['invoice_no__max'] or 0
                    order.invoice_no = last_invoice + 1
            elif new_status == 'Delivered':
                order.delivered_at = timezone.now()
                order.delivered_by = modifier_name
                order.delivered_comments = comments
            elif new_status == 'Cancelled' and order.payment_status == 'Pending':
                order.cancelled_at = timezone.now()
                order.cancelled_by = modifier_name
                order.cancelled_comments = comments
                order.payment_status = 'Cancelled'
            elif new_status == 'Cancelled' and order.payment_status == 'Successful':
                from management.models import Payment, Refund
                order.cancelled_at = timezone.now()
                order.cancelled_by = modifier_name
                order.cancelled_comments = comments
                
                payment = Payment.objects.filter(reference_order=order).first()
                if payment:
                    Refund.objects.create(
                        reference_order=order,
                        amount=order.total_amount,
                        payment_mode=payment.payment_mode,
                        customer_status=payment.transaction_type,
                        seller_status='Pending',
                        refund_status='Pending',
                        created_by=modifier_name,
                        cancellation_reason=comments
                    )
                    
                    # Create payment record for refund
                    refund_txn_id = f"RFND{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
                    Payment.objects.create(
                        transaction_id=refund_txn_id,
                        amount=order.total_amount,
                        status='Pending',
                        payment_mode=payment.payment_mode,
                        transaction_type='Refund',
                        reference_order=order,
                        avs_wallet_id=payment.avs_wallet_id,
                        refund_for=order.created_by,
                        created_by=modifier_name
                    )
            elif new_status == 'Cancelled':
                order.cancelled_at = timezone.now()
                order.cancelled_by = modifier_name
                order.cancelled_comments = comments
            
            order.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False})

def remove_product_image(request, image_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    if request.method == 'POST':
        try:
            image = ProductImage.objects.get(id=image_id)
            product = image.product
            
            if product.images.count() <= 1:
                return JsonResponse({'success': False, 'message': 'Cannot remove the last image'})
            
            was_primary = image.is_primary
            image.delete()
            
            if was_primary:
                first_image = product.images.first()
                if first_image:
                    first_image.is_primary = True
                    first_image.save()
            
            return JsonResponse({'success': True})
        except ProductImage.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Image not found'})
    
    return JsonResponse({'success': False})

def set_primary_image(request, image_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    if request.method == 'POST':
        try:
            image = ProductImage.objects.get(id=image_id)
            product = image.product
            
            product.images.update(is_primary=False)
            image.is_primary = True
            image.save()
            
            return JsonResponse({'success': True})
        except ProductImage.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Image not found'})
    
    return JsonResponse({'success': False})

def order_details(request, order_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    import json
    business_code = request.session.get('business_code')
    order = get_object_or_404(Order, order_id=order_id, sold_by=business_code)
    items = json.loads(order.items_details) if order.items_details else []
    
    username = request.session.get('user_id')
    current_user = StaffUser.objects.get(username=username)
    return render(request, 'seller/order_details.html', {'order': order, 'items': items, 'user': current_user})

def add_staff(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    business_code = request.session.get('business_code', 'B001')
    username = request.session.get('user_id')
    
    # Get business details for symbol and type
    business = BusinessDetail.objects.get(code=business_code)
    current_user = StaffUser.objects.get(username=username)
    current_staff = Staff.objects.get(username=current_user, business_code=business_code)
    is_admin = current_staff.staff_role in ['Seller-Admin', 'Shop-Admin', 'Admin']
    
    # Determine staff role based on business type
    allowed_role = 'Staff'  # Default
    
    # Generate next staff ID
    last_staff = Staff.objects.filter(business_code=business_code).order_by('-created_at').first()
    if last_staff:
        try:
            num_part = ''.join(filter(str.isdigit, last_staff.staff_id))
            if num_part:
                last_num = int(num_part)
                next_num = last_num + 1
            else:
                next_num = 1
        except:
            next_num = 1
    else:
        next_num = 1
    
    auto_staff_id = f"{business.symbol}{next_num:04d}"
    
    if request.method == 'POST':
        from seller.models import StaffPrivileges
        staff_role = request.POST.get('staff_role')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        staff_id = request.POST.get('staff_id', '')
        num_part = ''.join(filter(str.isdigit, staff_id))[-2:].zfill(2)
        username_new = (last_name[:2] + first_name[:4] + num_part).upper()
        phone_digits = ''.join(filter(str.isdigit, request.POST.get('phone', '')))
        auto_password = (first_name[:4] + last_name[:2] + phone_digits[-4:]).lower()

        user, created = StaffUser.objects.get_or_create(
            username=username_new,
            defaults={
                'first_name': first_name,
                'middle_name': request.POST.get('middle_name'),
                'last_name': last_name,
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone'),
                'password': auto_password
            }
        )
        
        # Update profile with address
        profile = user.profile
        profile.address1 = request.POST.get('address1')
        profile.address2 = request.POST.get('address2')
        profile.address3 = request.POST.get('address3')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.pin = request.POST.get('pin')
        profile.country = request.POST.get('country')
        profile.phone2 = request.POST.get('phone2')
        profile.dob = request.POST.get('dob') or None
        profile.aadhaar_number = request.POST.get('aadhaar_number')
        profile.pan_number = request.POST.get('pan_number').upper() if request.POST.get('pan_number') else ''
        if request.FILES.get('aadhaar_attachment'):
            profile.aadhaar_attachment = request.FILES['aadhaar_attachment']
        if request.FILES.get('pan_attachment'):
            profile.pan_attachment = request.FILES['pan_attachment']
        profile.save()
        
        staff = Staff.objects.create(
            username=user,
            staff_id=request.POST.get('staff_id'),
            business_code_id=business_code,
            role=staff_role,
            phone=request.POST.get('phone'),
            created_by=username
        )
        
        # Send SMS with password only (no username/seller code)
        print(f"[SMS to {request.POST.get('phone')}] Welcome to AVS! Your login password is: {auto_password}")
        
        # Create privileges for staff - Seller-Admin gets all privileges by default
        if staff_role == 'Admin':
            StaffPrivileges.objects.create(
                staff=staff,
                manage_orders=True,
                manage_products=True,
                manage_reports=True,
                manage_payments=True
            )
        else:
            StaffPrivileges.objects.create(
                staff=staff,
                manage_orders=request.POST.get('manage_orders') == 'on',
                manage_products=request.POST.get('manage_products') == 'on',
                manage_reports=request.POST.get('manage_reports') == 'on',
                manage_payments=request.POST.get('manage_payments') == 'on'
            )
        
        return redirect('/seller/?tab=staff#staff')
    
    return render(request, 'seller/add_staff.html', {
        'business_code': business_code,
        'auto_staff_id': auto_staff_id,
        'business_type': business.business_type,
        'is_admin': is_admin,
        'user': StaffUser.objects.get(username=request.session.get('user_id'))
    })

def view_staff(request, staff_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    from seller.models import StaffPrivileges
    business_code = request.session.get('business_code')
    staff = get_object_or_404(Staff, staff_id=staff_id, business_code=business_code)
    privileges = StaffPrivileges.objects.filter(staff=staff).first()
    
    username = request.session.get('user_id')
    current_user = StaffUser.objects.get(username=username)
    return render(request, 'seller/view_staff.html', {
        'staff': staff,
        'privileges': privileges,
        'business_code': business_code,
        'user': current_user
    })

def edit_staff(request, staff_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    from seller.models import StaffPrivileges
    business_code = request.session.get('business_code')
    staff = get_object_or_404(Staff, staff_id=staff_id, business_code=business_code)
    
    # Check if staff is Inactive - cannot edit Inactive staff
    if staff.status == 'Inactive':
        return redirect('view_staff', staff_id=staff_id)
    
    # Check if current user is trying to edit themselves and is admin
    current_username = request.session.get('user_id')
    is_editing_self = (staff.username.username == current_username)
    
    privileges, created = StaffPrivileges.objects.get_or_create(staff=staff)
    
    if request.method == 'POST':
        # Update StaffUser details
        staff.username.first_name = request.POST.get('first_name')
        staff.username.middle_name = request.POST.get('middle_name')
        staff.username.last_name = request.POST.get('last_name')
        staff.username.email = request.POST.get('email')
        staff.username.phone = request.POST.get('phone')
        staff.username.save()
        
        # Update Staff details
        staff.phone = request.POST.get('phone')
        staff.role = request.POST.get('staff_role')
        
        # Admin cannot change own status
        if not (is_editing_self and staff.role in ['Admin']):
            staff.status = request.POST.get('status')
        
        staff.modified_by = request.session.get('user_id')
        staff.save()
        
        # Update profile address
        profile = staff.username.profile
        profile.address1 = request.POST.get('address1')
        profile.address2 = request.POST.get('address2')
        profile.address3 = request.POST.get('address3')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.pin = request.POST.get('pin')
        profile.country = request.POST.get('country')
        profile.phone2 = request.POST.get('phone2')
        profile.dob = request.POST.get('dob') or None
        profile.aadhaar_number = request.POST.get('aadhaar_number')
        profile.pan_number = request.POST.get('pan_number').upper() if request.POST.get('pan_number') else ''
        if request.FILES.get('aadhaar_attachment'):
            profile.aadhaar_attachment = request.FILES['aadhaar_attachment']
        if request.FILES.get('pan_attachment'):
            profile.pan_attachment = request.FILES['pan_attachment']
        profile.save()
        
        # Update privileges - Seller-Admin always has all privileges
        if staff.role == 'Admin':
            privileges.manage_orders = True
            privileges.manage_products = True
            privileges.manage_reports = True
            privileges.manage_payments = True
        else:
            privileges.manage_orders = request.POST.get('manage_orders') == 'on'
            privileges.manage_products = request.POST.get('manage_products') == 'on'
            privileges.manage_reports = request.POST.get('manage_reports') == 'on'
            privileges.manage_payments = request.POST.get('manage_payments') == 'on'
        privileges.save()
        
        return redirect('view_staff', staff_id=staff_id)
    
    username = request.session.get('user_id')
    current_user = StaffUser.objects.get(username=username)
    return render(request, 'seller/edit_staff.html', {
        'staff': staff,
        'privileges': privileges,
        'business_code': business_code,
        'user': current_user
    })

def get_report(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return JsonResponse({'success': False})

    from management.models import Refund
    from django.db.models import Sum, Count

    business_code = request.session.get('business_code')
    report_type = request.GET.get('report_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    try:
        from django.utils.dateparse import parse_date
        from datetime import datetime, time
        import pytz
        from django.utils import timezone

        def make_dt(d, end=False):
            t = time.max if end else time.min
            return timezone.make_aware(datetime.combine(parse_date(d), t))

        rows = []
        summary = {}

        if report_type == 'orders':
            status_filter = request.GET.get('status', '')
            qs = Order.objects.filter(sold_by=business_code)
            if date_from: qs = qs.filter(created_at__gte=make_dt(date_from))
            if date_to:   qs = qs.filter(created_at__lte=make_dt(date_to, end=True))
            if status_filter: qs = qs.filter(order_status=status_filter)
            qs = qs.order_by('-created_at')
            summary = {
                'total': qs.count(),
                'revenue': str(qs.filter(order_status='Delivered', payment_status='Successful').aggregate(t=Sum('total_amount'))['t'] or 0)
            }
            rows = list(qs.values('order_id', 'customer_name', 'total_amount', 'payment_method', 'payment_status', 'order_status', 'created_at'))
            for r in rows:
                r['created_at'] = r['created_at'].strftime('%d %b %Y, %I:%M %p')
                r['total_amount'] = str(r['total_amount'])

        elif report_type == 'sales':
            qs = Order.objects.filter(sold_by=business_code, order_status='Delivered', payment_status='Successful')
            if date_from: qs = qs.filter(delivered_at__gte=make_dt(date_from))
            if date_to:   qs = qs.filter(delivered_at__lte=make_dt(date_to, end=True))
            qs = qs.order_by('-delivered_at')
            total = qs.aggregate(t=Sum('total_amount'))['t'] or 0
            summary = {'total_orders': qs.count(), 'total_revenue': str(total)}
            rows = list(qs.values('order_id', 'customer_name', 'total_amount', 'payment_method', 'delivered_at'))
            for r in rows:
                r['delivered_at'] = r['delivered_at'].strftime('%d %b %Y') if r['delivered_at'] else '-'
                r['total_amount'] = str(r['total_amount'])

        elif report_type == 'payments':
            from management.models import Payment
            status_filter = request.GET.get('status', '')
            qs = Payment.objects.filter(reference_order__sold_by=business_code)
            if date_from: qs = qs.filter(created_at__gte=make_dt(date_from))
            if date_to:   qs = qs.filter(created_at__lte=make_dt(date_to, end=True))
            if status_filter: qs = qs.filter(status=status_filter)
            qs = qs.order_by('-created_at')
            summary = {'total': qs.count(), 'amount': str(qs.aggregate(t=Sum('amount'))['t'] or 0)}
            rows = list(qs.values('transaction_id', 'amount', 'payment_mode', 'transaction_type', 'status', 'created_at', 'reference_order__order_id'))
            for r in rows:
                r['created_at'] = r['created_at'].strftime('%d %b %Y, %I:%M %p')
                r['amount'] = str(r['amount'])

        elif report_type == 'refunds':
            qs = Refund.objects.filter(reference_order__sold_by=business_code)
            if date_from: qs = qs.filter(created_at__gte=make_dt(date_from))
            if date_to:   qs = qs.filter(created_at__lte=make_dt(date_to, end=True))
            qs = qs.order_by('-created_at')
            summary = {'total': qs.count(), 'amount': str(qs.filter(refund_status='Refunded').aggregate(t=Sum('amount'))['t'] or 0)}
            rows = list(qs.values('reference_order__order_id', 'amount', 'payment_mode', 'refund_status', 'seller_status', 'created_at', 'refunded_at'))
            for r in rows:
                r['created_at'] = r['created_at'].strftime('%d %b %Y')
                r['refunded_at'] = r['refunded_at'].strftime('%d %b %Y') if r['refunded_at'] else '-'
                r['amount'] = str(r['amount'])

        elif report_type == 'inventory':
            qs = Product.objects.filter(business_code=business_code)
            stock_filter = request.GET.get('stock_filter', '')
            if stock_filter == 'low':    qs = qs.filter(stock__gt=0, stock__lt=5)
            elif stock_filter == 'out':  qs = qs.filter(stock=0)
            elif stock_filter == 'inactive': qs = qs.filter(status='Inactive')
            qs = qs.order_by('stock')
            summary = {'total': qs.count(), 'stock_value': str(qs.filter(status='Active').aggregate(v=Sum(models.F('stock') * models.F('selling_price')))['v'] or 0)}
            rows = list(qs.values('product_name', 'stock', 'selling_price', 'mrp', 'status', 'modified_at'))
            for r in rows:
                r['modified_at'] = r['modified_at'].strftime('%d %b %Y') if r['modified_at'] else '-'
                r['selling_price'] = str(r['selling_price'])
                r['mrp'] = str(r['mrp']) if r['mrp'] else '-'

        return JsonResponse({'success': True, 'rows': rows, 'summary': summary})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def update_seller_payment_status(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    if request.method == 'POST':
        import json
        from django.utils import timezone
        from management.models import Payment
        
        data = json.loads(request.body)
        order_id = data.get('order_id')
        seller_status = data.get('seller_status')
        comments = data.get('comments', '')
        
        username = request.session.get('user_id')
        user = StaffUser.objects.get(username=username)
        modifier_name = f"{user.first_name} {user.last_name}"
        
        try:
            order = Order.objects.get(order_id=order_id)
            
            if seller_status == 'Rejected':
                order.order_status = 'Cancelled'
                order.payment_status = 'Failed'
                order.cancelled_at = timezone.now()
                order.cancelled_by = modifier_name
                order.cancelled_comments = comments
                order.modified_by = modifier_name
                order.save()
                Payment.objects.filter(reference_order=order).update(status='Failed', modified_at=timezone.now(), modified_by=modifier_name)
            
            elif seller_status == 'Cancelled':
                order.order_status = 'Cancelled'
                order.payment_status = 'Cancelled'
                order.cancelled_at = timezone.now()
                order.cancelled_by = modifier_name
                order.cancelled_comments = comments
                order.modified_by = modifier_name
                order.save()
                Payment.objects.filter(reference_order=order).update(status='Cancelled', modified_at=timezone.now(), modified_by=modifier_name)
                
            elif seller_status in ['Credited', 'Refund']:
                order.payment_status = 'Successful'
                order.order_status = 'Confirmed'
                order.confirmed_at = timezone.now()
                order.confirmed_by = modifier_name
                order.confirmed_comments = comments
                order.modified_by = modifier_name
                order.save()
                Payment.objects.filter(reference_order=order).update(status='Successful', modified_at=timezone.now(), modified_by=modifier_name)
            
            return JsonResponse({'success': True})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'})
    
    return JsonResponse({'success': False})

def update_refund_status(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    if request.method == 'POST':
        import json
        from django.utils import timezone
        from management.models import Payment, Refund, Wallet
        from decimal import Decimal
        
        data = json.loads(request.body)
        refund_id = data.get('refund_id')
        seller_status = data.get('seller_status')
        refund_reason = data.get('refund_reason', '')
        
        username = request.session.get('user_id')
        user = StaffUser.objects.get(username=username)
        modifier_name = f"{user.first_name} {user.last_name}"
        
        try:
            refund = Refund.objects.get(id=refund_id)
            refund.seller_status = seller_status
            refund.refund_reason = refund_reason
            refund.modified_by = modifier_name
            refund.modified_at = timezone.now()
            
            if seller_status == 'Refund':
                refund.refund_status = 'Refunded'
                refund.refunded_by = modifier_name
                refund.refunded_at = timezone.now()
                
                # Update Payment table - set refund payment to Successful
                Payment.objects.filter(
                    reference_order=refund.reference_order,
                    transaction_type='Refund'
                ).update(
                    status='Successful',
                    processing_at=timezone.now(),
                    processing_by=modifier_name,
                    modified_at=timezone.now(),
                    modified_by=modifier_name
                )
                
                # Credit wallet if payment was made via wallet
                if refund.payment_mode == 'Wallet':
                    original_payment = Payment.objects.filter(
                        reference_order=refund.reference_order,
                        transaction_type='Debit'
                    ).first()
                    
                    if original_payment and original_payment.avs_wallet_id:
                        wallet = Wallet.objects.filter(wallet_id=original_payment.avs_wallet_id).first()
                        if wallet:
                            wallet.wallet_amount += Decimal(str(refund.amount))
                            wallet.modified_by = modifier_name
                            wallet.save()
                
            elif seller_status == 'Reject':
                refund.refund_status = 'Rejected'
                Payment.objects.filter(
                    reference_order=refund.reference_order,
                    transaction_type='Refund'
                ).update(
                    status='Failed',
                    modified_at=timezone.now(),
                    modified_by=modifier_name
                )
            elif seller_status == 'Cancelled':
                refund.refund_status = 'Cancelled'
                Payment.objects.filter(
                    reference_order=refund.reference_order,
                    transaction_type='Refund'
                ).update(
                    status='Cancelled',
                    modified_at=timezone.now(),
                    modified_by=modifier_name
                )
            
            refund.save()
            return JsonResponse({'success': True})
        except Refund.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Refund not found'})
    
    return JsonResponse({'success': False})


def staff_change_password(request, username):
    if not request.session.get('is_logged_in'):
        return redirect('staff_login')
    user = StaffUser.objects.get(username=username)
    error, success = None, None
    if request.method == 'POST':
        current = request.POST.get('current_password')
        new_pw = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')
        if user.password != current:
            error = 'Current password is incorrect'
        elif new_pw != confirm:
            error = 'New passwords do not match'
        elif len(new_pw) < 6:
            error = 'Password must be at least 6 characters'
        else:
            user.password = new_pw
            user.save()
            success = 'Password changed successfully'
    return render(request, 'seller/change_password.html', {'user': user, 'error': error, 'success': success})


def send_otp_email(request):
    if not request.session.get('is_logged_in') or request.method != 'POST':
        return JsonResponse({'success': False})
    import json, random
    data = json.loads(request.body)
    step = data.get('step')  # 'existing' or 'new'
    new_email = data.get('email', '')
    otp = str(random.randint(100000, 999999))
    if step == 'existing':
        username = request.session.get('user_id')
        user = StaffUser.objects.get(username=username)
        request.session['otp_existing_email'] = otp
        print(f"[OTP] Existing email OTP for {user.email}: {otp}")
    else:
        request.session['otp_new_email'] = otp
        request.session['pending_new_email'] = new_email
        print(f"[OTP] New email OTP for {new_email}: {otp}")
    return JsonResponse({'success': True})


def verify_otp_email(request):
    if not request.session.get('is_logged_in') or request.method != 'POST':
        return JsonResponse({'success': False})
    import json
    data = json.loads(request.body)
    step = data.get('step')
    otp_entered = data.get('otp', '')
    if step == 'existing':
        if otp_entered == request.session.get('otp_existing_email'):
            del request.session['otp_existing_email']
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Invalid OTP'})
    else:
        if otp_entered == request.session.get('otp_new_email'):
            username = request.session.get('user_id')
            new_email = request.session.get('pending_new_email')
            StaffUser.objects.filter(username=username).update(email=new_email)
            del request.session['otp_new_email']
            del request.session['pending_new_email']
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Invalid OTP'})


def send_otp_phone(request):
    if not request.session.get('is_logged_in') or request.method != 'POST':
        return JsonResponse({'success': False})
    import json, random
    data = json.loads(request.body)
    step = data.get('step')
    new_phone = data.get('phone', '')
    otp = str(random.randint(100000, 999999))
    if step == 'existing':
        username = request.session.get('user_id')
        user = StaffUser.objects.get(username=username)
        request.session['otp_existing_phone'] = otp
        print(f"[OTP] Existing phone OTP for {user.phone}: {otp}")
    else:
        request.session['otp_new_phone'] = otp
        request.session['pending_new_phone'] = new_phone
        print(f"[OTP] New phone OTP for {new_phone}: {otp}")
    return JsonResponse({'success': True})


def verify_otp_phone(request):
    if not request.session.get('is_logged_in') or request.method != 'POST':
        return JsonResponse({'success': False})
    import json
    data = json.loads(request.body)
    step = data.get('step')
    otp_entered = data.get('otp', '')
    if step == 'existing':
        if otp_entered == request.session.get('otp_existing_phone'):
            del request.session['otp_existing_phone']
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Invalid OTP'})
    else:
        if otp_entered == request.session.get('otp_new_phone'):
            username = request.session.get('user_id')
            new_phone = request.session.get('pending_new_phone')
            StaffUser.objects.filter(username=username).update(phone=new_phone)
            del request.session['otp_new_phone']
            del request.session['pending_new_phone']
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Invalid OTP'})
