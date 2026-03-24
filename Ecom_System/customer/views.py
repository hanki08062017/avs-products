from django.shortcuts import render, redirect, get_object_or_404
from management.models import Product, ProductCategory, Order, BusinessDetail, GSTDetail, DeliveryZone, DeliverySettings
from customer.models import Customer
from seller.models import StaffUser
from django.db.models import Q

def home(request):
    from collections import defaultdict
    
    categories = ProductCategory.objects.all()
    products = Product.objects.filter(status='Active')
    
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')
    
    if category_filter:
        products = products.filter(product_category__category=category_filter)
    
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(product_category__category__icontains=search_query) |
            Q(product_category__sub_category__icontains=search_query)
        )
    
    # Group products by category when no search
    products_by_category = defaultdict(list)
    if not search_query:
        for product in products:
            products_by_category[product.category].append(product)
    
    # Get user if logged in
    user = None
    if request.session.get('is_logged_in'):
        username = request.session.get('user_id')
        user_type = request.session.get('user_type')
        if user_type == 'customer':
            user = Customer.objects.filter(username=username).first()
        elif user_type == 'staff':
            user = StaffUser.objects.filter(username=username).first()
    
    return render(request, 'customer/home.html', {
        'products': products,
        'categories': categories,
        'products_by_category': dict(products_by_category),
        'search_query': search_query,
        'user': user
    })


def customer_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = Customer.objects.get(username=username, password=password)
            request.session['user_id'] = username
            request.session['is_logged_in'] = True
            request.session['user_type'] = 'customer'
            
            next_url = request.session.pop('next', None)
            if next_url:
                return redirect(next_url)
            return redirect('home')
        except Customer.DoesNotExist:
            return render(request, 'customer/customer_login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'customer/customer_login.html')


def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            return render(request, 'customer/signup.html', {'error': 'Passwords do not match'})
        
        try:
            if Customer.objects.filter(username=username).exists():
                return render(request, 'customer/signup.html', {'error': 'Username already exists'})
            
            if Customer.objects.filter(email=email).exists():
                return render(request, 'customer/signup.html', {'error': 'Email already exists'})
            
            customer = Customer.objects.create(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                email=email,
                phone=phone,
                username=username,
                password=password
            )
            
            request.session['user_id'] = username
            request.session['is_logged_in'] = True
            request.session['user_type'] = 'customer'
            return redirect('home')
        except Exception as e:
            return render(request, 'customer/signup.html', {'error': str(e)})
    
    return render(request, 'customer/signup.html')


def check_username(request):
    from django.http import JsonResponse
    username = request.GET.get('username', '').strip()
    if not username:
        return JsonResponse({'available': False})
    exists = Customer.objects.filter(username=username).exists()
    return JsonResponse({'available': not exists})


def customer_logout_view(request):
    request.session.flush()
    return redirect('home')


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'customer/product_detail.html', {'product': product})


def checkout(request):
    if not request.session.get('is_logged_in'):
        request.session['next'] = '/checkout/'
        return redirect('login')
    
    # Get user
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    user_pin = user.profile.pin if user and user.profile else ''
    business = BusinessDetail.objects.first()
    delivery_settings, _ = DeliverySettings.objects.get_or_create(business_code=business)
    delivery_zone = DeliveryZone.objects.filter(business_code=business, pincode_to=user_pin, status='Active').first()
    min_amount_free_delivery = float(delivery_settings.min_amount_free_delivery or 0)
    max_distance_km = float(delivery_settings.max_distance_km or 0)
    base_charge = float(delivery_zone.base_charge) if delivery_zone else 0
    delivery_free = delivery_settings.delivery_free
    ship_free = delivery_settings.ship_free
    
    import json
    delivery_data = json.dumps({'min_amount_free_delivery': min_amount_free_delivery, 'base_charge': base_charge, 'max_distance_km' : max_distance_km, 'delivery_free': delivery_free, 'ship_free': ship_free})
    return render(request, 'customer/checkout.html', {'user': user, 'delivery_data': delivery_data})


def place_order(request):
    if not request.session.get('is_logged_in'):
        request.session['next'] = '/place-order/'
        return redirect('login')
    
    if request.method == 'POST':
        from customer.models import Customer, SavedAddress
        
        username = request.session.get('user_id')
        customer = Customer.objects.get(username=username)
        
        same_as_billing = request.POST.get('same_as_billing') == 'true'
        # Handle billing address
        if request.POST.get('is_new_billing') == 'true':
            addr_type = 'Both' if same_as_billing else 'Billing'
            count_field = 'Both' if same_as_billing else 'Billing'
            billing_count = SavedAddress.objects.filter(customer=customer, address_type=count_field).count()
            if billing_count >= 5:
                oldest = SavedAddress.objects.filter(customer=customer, address_type=count_field).order_by('created_at').first()
                if oldest:
                    oldest.delete()
            SavedAddress.objects.create(
                customer=customer,
                address_type=addr_type,
                name=request.POST.get('bill_name'),
                phone=request.POST.get('bill_phone'),
                address1=request.POST.get('bill_address1'),
                address2=request.POST.get('bill_address2'),
                city=request.POST.get('bill_city'),
                state=request.POST.get('bill_state'),
                pin=request.POST.get('bill_pin'),
                country=request.POST.get('bill_country'),
                is_default=False
            )
        elif request.POST.get('is_new_billing') == 'update':
            bill_addr_id = request.POST.get('bill_address_id')
            if bill_addr_id:
                update_fields = dict(
                    name=request.POST.get('bill_name'),
                    phone=request.POST.get('bill_phone'),
                    address1=request.POST.get('bill_address1'),
                    address2=request.POST.get('bill_address2'),
                    city=request.POST.get('bill_city'),
                    state=request.POST.get('bill_state'),
                    pin=request.POST.get('bill_pin'),
                    country=request.POST.get('bill_country')
                )
                if same_as_billing:
                    update_fields['address_type'] = 'Both'
                SavedAddress.objects.filter(id=bill_addr_id).update(**update_fields)

        # Handle shipping address — skip if same_as_billing (billing already saved as 'Both')
        if not same_as_billing:
            if request.POST.get('is_new_shipping') == 'true':
                shipping_count = SavedAddress.objects.filter(customer=customer, address_type='Shipping').count()
                if shipping_count >= 5:
                    oldest = SavedAddress.objects.filter(customer=customer, address_type='Shipping').order_by('created_at').first()
                    if oldest:
                        oldest.delete()
                SavedAddress.objects.create(
                    customer=customer,
                    address_type='Shipping',
                    name=request.POST.get('ship_name'),
                    phone=request.POST.get('ship_phone'),
                    address1=request.POST.get('ship_address1'),
                    address2=request.POST.get('ship_address2'),
                    city=request.POST.get('ship_city'),
                    state=request.POST.get('ship_state'),
                    pin=request.POST.get('ship_pin'),
                    country=request.POST.get('ship_country'),
                    is_default=False
                )
            elif request.POST.get('is_new_shipping') == 'update':
                ship_addr_id = request.POST.get('ship_address_id')
                if ship_addr_id:
                    SavedAddress.objects.filter(id=ship_addr_id).update(
                        name=request.POST.get('ship_name'),
                        phone=request.POST.get('ship_phone'),
                        address1=request.POST.get('ship_address1'),
                        address2=request.POST.get('ship_address2'),
                        city=request.POST.get('ship_city'),
                        state=request.POST.get('ship_state'),
                        pin=request.POST.get('ship_pin'),
                        country=request.POST.get('ship_country')
                    )
        
        # Store order data in session
        request.session['order_data'] = {
            'customer_name': request.POST.get('customer_name'),
            'customer_email': request.POST.get('customer_email'),
            'customer_phone': request.POST.get('customer_phone'),
            'bill_name': request.POST.get('bill_name'),
            'bill_phone': request.POST.get('bill_phone'),
            'bill_address1': request.POST.get('bill_address1'),
            'bill_address2': request.POST.get('bill_address2'),
            'bill_city': request.POST.get('bill_city'),
            'bill_state': request.POST.get('bill_state'),
            'bill_pin': request.POST.get('bill_pin'),
            'bill_country': request.POST.get('bill_country'),
            'ship_name': request.POST.get('ship_name'),
            'ship_phone': request.POST.get('ship_phone'),
            'ship_address1': request.POST.get('ship_address1'),
            'ship_address2': request.POST.get('ship_address2'),
            'ship_city': request.POST.get('ship_city'),
            'ship_state': request.POST.get('ship_state'),
            'ship_pin': request.POST.get('ship_pin'),
            'ship_country': request.POST.get('ship_country'),
            'payment_method': request.POST.get('payment_method'),
            'cart_data': request.POST.get('cart_data'),
            'total_amount': request.POST.get('total_amount')
        }
        return redirect('confirm_order')
    
    # Load saved addresses
    from customer.models import Customer, SavedAddress
    username = request.session.get('user_id')
    customer = Customer.objects.get(username=username)
    user = customer
    customer_address = user.profile
    billing_addresses = SavedAddress.objects.filter(customer=customer, address_type__in=['Billing', 'Both']).order_by('-is_default', '-created_at')[:5]
    shipping_addresses = SavedAddress.objects.filter(customer=customer, address_type__in=['Shipping', 'Both']).order_by('-is_default', '-created_at')[:5]
    
    import json
    business = BusinessDetail.objects.first()
    delivery_settings, _ = DeliverySettings.objects.get_or_create(business_code=business)
    default_shipping = shipping_addresses.first()
    user_pin = default_shipping.pin if default_shipping else (customer_address.pin if customer_address else '')
    delivery_zone = DeliveryZone.objects.filter(business_code=business, pincode_to=user_pin, status='Active').first()
    min_amount_free_delivery = float(delivery_settings.min_amount_free_delivery or 0)
    max_distance_km = float(delivery_settings.max_distance_km or 0)
    base_charge = float(delivery_zone.base_charge) if delivery_zone else 0
    delivery_free = delivery_settings.delivery_free
    ship_free = delivery_settings.ship_free
    delivery_data = json.dumps({'min_amount_free_delivery': min_amount_free_delivery, 'base_charge': base_charge, 'max_distance_km': max_distance_km, 'delivery_free': delivery_free, 'ship_free': ship_free})

    return render(request, 'customer/place_order.html', {
        'billing_addresses': billing_addresses,
        'shipping_addresses': shipping_addresses,
        'customer_address': customer_address,
        'customer': customer,
        'user': user,
        'delivery_settings': delivery_settings,
        'delivery_zones': delivery_data,
        'delivery_data': delivery_data,
    })


def profile_view(request, username):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    session_username = request.session.get('user_id')
    if session_username != username:
        return redirect('home')
    
    try:
        user = Customer.objects.get(username=username)
        profile = user.profile

        if request.method == 'POST':
            user.first_name = request.POST.get('first_name')
            user.middle_name = request.POST.get('middle_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.phone = request.POST.get('phone')
            user.save()
            
            # Handle profile picture upload
            if request.FILES.get('profile_picture'):
                profile.profile_pic = request.FILES['profile_picture']
            
            profile.address1 = request.POST.get('address1')
            profile.address2 = request.POST.get('address2')
            profile.city = request.POST.get('city')
            profile.state = request.POST.get('state')
            profile.pin = request.POST.get('pin')
            profile.country = request.POST.get('country')
            profile.phone1 = request.POST.get('phone1')
            profile.phone2 = request.POST.get('phone2')
            profile.save()
            
            request.session['profile_success'] = 'Profile updated successfully'
            return redirect('profile', username=username)
        
        from customer.models import SavedAddress
        billing_addresses = SavedAddress.objects.filter(customer=user, address_type__in=['Billing', 'Both']).order_by('-is_default', '-created_at')
        shipping_addresses = SavedAddress.objects.filter(customer=user, address_type__in=['Shipping', 'Both']).order_by('-is_default', '-created_at')
        
        success = request.session.pop('profile_success', None)
        return render(request, 'customer/customer_profile.html', {
            'user': user, 
            'profile': profile, 
            'success': success,
            'billing_addresses': billing_addresses,
            'shipping_addresses': shipping_addresses
        })
    except (Customer.DoesNotExist):
        return redirect('login')


def _build_delivery_data(ship_pin):
    import json
    business = BusinessDetail.objects.first()
    delivery_settings, _ = DeliverySettings.objects.get_or_create(business_code=business)
    delivery_zone = DeliveryZone.objects.filter(business_code=business, pincode_to=ship_pin, status='Active').first()
    return {
        'min_amount_free_delivery': float(delivery_settings.min_amount_free_delivery or 0),
        'base_charge': float(delivery_zone.base_charge) if delivery_zone else 0,
        'max_distance_km': float(delivery_settings.max_distance_km or 0),
        'delivery_free': delivery_settings.delivery_free,
        'ship_free': delivery_settings.ship_free,
    }

def _calc_delivery_charge(dd, items):
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    total_ship = sum(item.get('ship', 0) for item in items)
    ship_charge = 0 if dd['ship_free'] else total_ship
    delivery_charge = 0 if dd['delivery_free'] else dd['base_charge']
    min_charges = ship_charge + delivery_charge
    return 0 if (dd['min_amount_free_delivery'] > 0 and subtotal >= dd['min_amount_free_delivery']) else min_charges

def confirm_order(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    
    order_data = request.session.get('order_data')
    if not order_data:
        return redirect('home')
    
    if request.method == 'POST':
        from django.utils import timezone
        import json
        from collections import defaultdict
        
        payment_method = request.POST.get('payment_method')
        cart_data_raw = order_data.get('cart_data')
        if not cart_data_raw:
            return redirect('home')
        cart_data = json.loads(cart_data_raw)
        dd = _build_delivery_data(order_data.get('ship_pin', ''))
        
        # Group items by seller
        items_by_seller = defaultdict(list)
        for item in cart_data.values():
            try:
                product = Product.objects.get(id=item['id'])
                if product.business_code:
                    seller_code = product.business_code.code
                else:
                    seller_code = BusinessDetail.objects.first().code
                items_by_seller[seller_code].append({
                    'id': item['id'],
                    'name': f"{item['name']} - {item['qty']}{item['unit']}",
                    'quantity': item['quantity'],
                    'price': float(item['price']),
                    'mrp': float(product.mrp),
                    'base_price': float(product.base_price),
                    'gst': float(product.gst),
                    'hsn': product.product_category.hsn
                })
            except Product.DoesNotExist:
                seller_code = BusinessDetail.objects.first().code
                items_by_seller[seller_code].append(item)
        
        # Build all items with ship for delivery calc
        all_items_with_ship = []
        for item in cart_data.values():
            try:
                product = Product.objects.get(id=item['id'])
                all_items_with_ship.append({'price': float(item['price']), 'quantity': item['quantity'], 'ship': float(product.ship_cost or 0)})
            except Product.DoesNotExist:
                all_items_with_ship.append({'price': float(item['price']), 'quantity': item['quantity'], 'ship': 0})
        total_delivery = _calc_delivery_charge(dd, all_items_with_ship)
        created_orders = []
        num_sellers = len(items_by_seller)
        for seller_code, items in items_by_seller.items():
            seller_subtotal = sum(item['price'] * item['quantity'] for item in items)
            delivery_charge = round(total_delivery / num_sellers, 2)
            seller_total = seller_subtotal + delivery_charge
            order_id = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
            order = Order.objects.create(
                order_id=order_id,
                customer_name=order_data['customer_name'],
                customer_email=order_data['customer_email'],
                customer_phone=order_data['customer_phone'],
                bill_name=order_data['bill_name'],
                bill_phone=order_data['bill_phone'],
                bill_address1=order_data['bill_address1'],
                bill_address2=order_data['bill_address2'] or '',
                bill_city=order_data['bill_city'],
                bill_state=order_data['bill_state'],
                bill_pin=order_data['bill_pin'],
                bill_country=order_data['bill_country'],
                ship_name=order_data['ship_name'],
                ship_phone=order_data['ship_phone'],
                ship_address1=order_data['ship_address1'],
                ship_address2=order_data['ship_address2'] or '',
                ship_city=order_data['ship_city'],
                ship_state=order_data['ship_state'],
                ship_pin=order_data['ship_pin'],
                ship_country=order_data['ship_country'],
                total_amount=seller_total,
                delivery_charge=delivery_charge,
                sold_by=seller_code,
                payment_method=payment_method,
                payment_status='Pending',
                placed_type='Online',
                placed_at=timezone.now(),
                placed_by=request.session.get('user_id'),
                order_status='Placed',
                created_by=request.session.get('user_id'),
                items_details=json.dumps(items)
            )
            for item in items:
                try:
                    product = Product.objects.get(id=item['id'])
                    product.stock -= item['quantity']
                    product.save()
                except Product.DoesNotExist:
                    pass
            created_orders.append(order)
        
        del request.session['order_data']
        return render(request, 'customer/order_success.html', {'orders': created_orders, 'user': user})
    
    import json
    dd = _build_delivery_data(order_data.get('ship_pin', ''))
    delivery_data = json.dumps(dd)
    return render(request, 'customer/confirm_order.html', {'order_data': order_data, 'user': user, 'delivery_data': delivery_data})


def process_payment(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    order_data = request.session.get('order_data')
    if not order_data:
        return redirect('confirm_order')
    
    if request.method == 'POST':
        from django.utils import timezone
        from customer.models import Customer, SavedPaymentMethod
        import json
        from collections import defaultdict
        
        payment_method = request.POST.get('payment_method')
        username = request.session.get('user_id')
        try:
            customer = Customer.objects.get(username=username)
            user = customer
        except Customer.DoesNotExist:
            return redirect('login')
        
        # Save payment method
        if payment_method == 'Card':
            card_number = request.POST.get('card_number')
            SavedPaymentMethod.objects.update_or_create(
                customer=customer,
                payment_type='Card',
                defaults={
                    'card_last4': card_number[-4:] if card_number else '',
                    'card_name': request.POST.get('card_name'),
                    'is_default': True
                }
            )
        elif payment_method == 'UPI':
            SavedPaymentMethod.objects.update_or_create(
                customer=customer,
                payment_type='UPI',
                defaults={
                    'upi_id': request.POST.get('upi_id'),
                    'is_default': True
                }
            )
        
        cart_data_raw = order_data.get('cart_data')
        if not cart_data_raw:
            return redirect('home')
        cart_data = json.loads(cart_data_raw)
        avs_wallet_id = request.POST.get('avs_wallet_id', '')
        normal_wallet_id = request.POST.get('normal_wallet_id', '')
        
        # Verify OTP for AVS wallet payment
        if payment_method == 'Wallet' and avs_wallet_id:
            from management.models import Wallet as WalletModel
            wallet = WalletModel.objects.filter(wallet_id=avs_wallet_id).first()
            if wallet and wallet.wallet_type == 'AVS':
                # Check if OTP was verified
                if not request.session.get(f'payment_verified_{avs_wallet_id}'):
                    return render(request, 'customer/process_payment.html', {
                        'order_data': order_data,
                        'saved_card': SavedPaymentMethod.objects.filter(customer=customer, payment_type='Card', is_default=True).first(),
                        'saved_upi': SavedPaymentMethod.objects.filter(customer=customer, payment_type='UPI', is_default=True).first(),
                        'normal_wallet': WalletModel.objects.filter(user_id=customer, wallet_type='Other').first(),
                        'avs_wallets': WalletModel.objects.filter(user_id=customer, wallet_type='AVS'),
                        'user': user,
                        'error': 'OTP verification required for AVS wallet payment'
                    })
                # Clear verification flag
                del request.session[f'payment_verified_{avs_wallet_id}']
        
        # Group items by seller
        items_by_seller = defaultdict(list)
        for item in cart_data.values():
            try:
                product = Product.objects.get(id=item['id'])
                # Use product's business_code if available, otherwise use first available business
                if product.business_code:
                    seller_code = product.business_code.code
                else:
                    # Get first business code as fallback
                    first_business = BusinessDetail.objects.first()
                    seller_code = first_business.code
                items_by_seller[seller_code].append({
                    'id': item['id'],
                    'name': f"{item['name']} - {item['qty']}{item['unit']}",
                    'quantity': item['quantity'],
                    'price': float(item['price']),
                    'mrp': float(product.mrp),
                    'base_price': float(product.base_price),
                    'gst': float(product.gst),
                    'hsn': product.product_category.hsn
                })
            except Product.DoesNotExist:
                # Use first business code as fallback
                first_business = BusinessDetail.objects.first()
                seller_code = first_business.code
                items_by_seller[seller_code].append(item)
        
        dd = _build_delivery_data(order_data.get('ship_pin', ''))
        # Calc total delivery from full cart
        all_items_with_ship = []
        for item in cart_data.values():
            try:
                product = Product.objects.get(id=item['id'])
                all_items_with_ship.append({'price': float(item['price']), 'quantity': item['quantity'], 'ship': float(product.ship_cost or 0)})
            except Product.DoesNotExist:
                all_items_with_ship.append({'price': float(item['price']), 'quantity': item['quantity'], 'ship': 0})
        total_delivery = _calc_delivery_charge(dd, all_items_with_ship)
        created_orders = []
        num_sellers = len(items_by_seller)
        for seller_code, items in items_by_seller.items():
            seller_subtotal = sum(item['price'] * item['quantity'] for item in items)
            delivery_charge = round(total_delivery / num_sellers, 2)
            seller_total = seller_subtotal + delivery_charge
            order_id = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
            
            order = Order.objects.create(
                order_id=order_id,
                customer_name=order_data['customer_name'],
                customer_email=order_data['customer_email'],
                customer_phone=order_data['customer_phone'],
                bill_name=order_data['bill_name'],
                bill_phone=order_data['bill_phone'],
                bill_address1=order_data['bill_address1'],
                bill_address2=order_data['bill_address2'] or '',
                bill_city=order_data['bill_city'],
                bill_state=order_data['bill_state'],
                bill_pin=order_data['bill_pin'],
                bill_country=order_data['bill_country'],
                ship_name=order_data['ship_name'],
                ship_phone=order_data['ship_phone'],
                ship_address1=order_data['ship_address1'],
                ship_address2=order_data['ship_address2'] or '',
                ship_city=order_data['ship_city'],
                ship_state=order_data['ship_state'],
                ship_pin=order_data['ship_pin'],
                ship_country=order_data['ship_country'],
                total_amount=seller_total,
                delivery_charge=delivery_charge,
                sold_by=seller_code,
                payment_method=payment_method,
                payment_status='Successful',
                placed_type='Online',
                placed_at=timezone.now(),
                order_status='Confirmed',
                confirmed_at=timezone.now(),
                confirmed_by='System',
                created_by=username,
                items_details=json.dumps(items)
            )
            
            # Create payment record for each order
            from management.models import Payment
            transaction_id = f"TXN{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
            Payment.objects.create(
                transaction_id=transaction_id,
                amount=seller_total,
                status='Successful',
                payment_mode=payment_method,
                transaction_type='Debit',
                reference_order=order,
                avs_wallet_id=avs_wallet_id if payment_method == 'Wallet' else None,
                created_by=username
            )
            
            # Deduct amount from wallet if wallet payment
            if payment_method == 'Wallet':
                from management.models import Wallet as WalletModel, WalletTransaction
                from decimal import Decimal
                seller_total_decimal = Decimal(str(seller_total))
                if avs_wallet_id:
                    avs_wallet = WalletModel.objects.filter(wallet_id=avs_wallet_id).first()
                    if avs_wallet:
                        avs_deduct = min(avs_wallet.wallet_amount, seller_total_decimal)
                        avs_wallet.wallet_amount -= avs_deduct
                        avs_wallet.modified_by = username
                        avs_wallet.save()
                        WalletTransaction.objects.create(
                            transaction_id=transaction_id,
                            avs_customer_name=avs_wallet.customer_name,
                            avs_customer_id=avs_wallet.customer_id,
                            avs_customer_mobile=avs_wallet.customer_mobile,
                            transaction_type='Debit',
                            amount=avs_deduct,
                            reference_order=order,
                            transaction_date=timezone.now(),
                            transaction_for='Order Payment',
                            transaction_by=username,
                        )
                        remaining = seller_total_decimal - avs_deduct
                        if remaining > 0 and normal_wallet_id:
                            normal_wallet = WalletModel.objects.filter(wallet_id=normal_wallet_id).first()
                            if normal_wallet and normal_wallet.wallet_amount >= remaining:
                                normal_wallet.wallet_amount -= remaining
                                normal_wallet.modified_by = username
                                normal_wallet.save()
                            else:
                                order.payment_status = 'Failed'
                                order.save()
                                Payment.objects.filter(transaction_id=transaction_id).update(status='Failed')
                elif normal_wallet_id:
                    normal_wallet = WalletModel.objects.filter(wallet_id=normal_wallet_id).first()
                    if normal_wallet and normal_wallet.wallet_amount >= seller_total_decimal:
                        normal_wallet.wallet_amount -= seller_total_decimal
                        normal_wallet.modified_by = username
                        normal_wallet.save()
                    else:
                        order.payment_status = 'Failed'
                        order.save()
                        Payment.objects.filter(transaction_id=transaction_id).update(status='Failed')
            
            # Reduce stock for each item
            for item in items:
                try:
                    product = Product.objects.get(id=item['id'])
                    product.stock -= item['quantity']
                    product.save()
                except Product.DoesNotExist:
                    pass
            
            created_orders.append(order)
        
        del request.session['order_data']
        return render(request, 'customer/order_success.html', {'orders': created_orders, 'user': user})
    
    # Load saved payment methods
    from customer.models import Customer, SavedPaymentMethod
    from management.models import Wallet
    username = request.session.get('user_id')
    try:
        customer = Customer.objects.get(username=username)
        user = customer
        saved_card = SavedPaymentMethod.objects.filter(customer=customer, payment_type='Card', is_default=True).first()
        saved_upi = SavedPaymentMethod.objects.filter(customer=customer, payment_type='UPI', is_default=True).first()
        normal_wallet = Wallet.objects.filter(user_id=customer, wallet_type='Other').first()
        avs_wallets = Wallet.objects.filter(user_id=customer, wallet_type='AVS')
    except Customer.DoesNotExist:
        return redirect('login')
    
    import json
    dd = _build_delivery_data(order_data.get('ship_pin', ''))
    delivery_data = json.dumps(dd)
    return render(request, 'customer/process_payment.html', {
        'order_data': order_data,
        'saved_card': saved_card,
        'saved_upi': saved_upi,
        'normal_wallet': normal_wallet,
        'avs_wallets': avs_wallets,
        'user': user,
        'delivery_data': delivery_data,
    })


def order_history(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    orders = Order.objects.filter(created_by=username).order_by('-created_at')
    
    return render(request, 'customer/order_history.html', {'orders': orders, 'user': user})


def wallet_view(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    from management.models import Wallet, Payment
    from django.http import JsonResponse
    import random
    
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify_customer':
            customer_id = request.POST.get('customer_id')
            try:
                wallet = Wallet.objects.get(customer_id=customer_id)
                # Send OTP immediately after verification
                otp = random.randint(100000, 999999)
                request.session['wallet_otp'] = otp
                request.session['wallet_customer_id'] = customer_id
                request.session['wallet_customer_name'] = wallet.customer_name
                request.session['wallet_customer_mobile'] = wallet.customer_mobile
                return JsonResponse({'success': True, 'name': wallet.customer_name, 'otp_sent': True, 'message': f'OTP sent (Demo: {otp})'})
            except Wallet.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Customer ID not found in wallet records'})
        
        elif action == 'send_otp':
            otp = random.randint(100000, 999999)
            request.session['wallet_otp'] = otp
            request.session['wallet_amount'] = request.POST.get('amount')
            request.session['wallet_type'] = request.POST.get('wallet_type')
            request.session['wallet_customer_id'] = request.POST.get('customer_id', '')
            request.session['wallet_customer_name'] = request.POST.get('customer_name', '')
            request.session['wallet_customer_mobile'] = request.POST.get('customer_mobile', '')
            return JsonResponse({'success': True, 'message': f'OTP sent (Demo: {otp})'})
        
        elif action == 'verify_otp':
            otp = request.POST.get('otp')
            if str(request.session.get('wallet_otp')) == otp:
                customer_id = request.session.get('wallet_customer_id')
                customer_name = request.session.get('wallet_customer_name')
                customer_mobile = request.session.get('wallet_customer_mobile')
                
                # Get the wallet for this customer and link it to current user
                wallet = Wallet.objects.filter(customer_id=customer_id).first()
                if wallet:
                    wallet.user_id = user
                    wallet.save()
                
                # Clear session data
                del request.session['wallet_otp']
                del request.session['wallet_customer_id']
                del request.session['wallet_customer_name']
                del request.session['wallet_customer_mobile']
                
                return JsonResponse({'success': True, 'message': 'Wallet linked successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid OTP'})
        
        elif action == 'remove_avs_wallet':
            wallet_id = request.POST.get('wallet_id')
            try:
                wallet = Wallet.objects.get(wallet_id=wallet_id, user_id=user)
                wallet.user_id = None  # Untag from user
                wallet.save()
                return JsonResponse({'success': True, 'message': 'AVS wallet removed successfully'})
            except Wallet.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Wallet not found'})
        
        elif action == 'send_payment_otp':
            wallet_id = request.POST.get('wallet_id')
            customer_id = request.POST.get('customer_id')
            try:
                wallet = Wallet.objects.get(wallet_id=wallet_id, customer_id=customer_id)
                otp = random.randint(100000, 999999)
                request.session[f'payment_otp_{wallet_id}'] = otp
                return JsonResponse({'success': True, 'message': f'OTP sent to {wallet.customer_mobile}', 'demo_otp': otp})
            except Wallet.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Wallet not found'})
        
        elif action == 'verify_payment_otp':
            wallet_id = request.POST.get('wallet_id')
            otp = request.POST.get('otp')
            session_otp = request.session.get(f'payment_otp_{wallet_id}')
            
            if str(session_otp) == otp:
                # OTP verified, mark as verified
                request.session[f'payment_verified_{wallet_id}'] = True
                del request.session[f'payment_otp_{wallet_id}']
                return JsonResponse({'success': True, 'message': 'OTP verified successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid OTP'})
        
        elif action == 'remove_wallet':
            wallet_id = request.POST.get('wallet_id')
            try:
                wallet = Wallet.objects.get(wallet_id=wallet_id)
                wallet.delete()
                return JsonResponse({'success': True, 'message': 'Wallet removed successfully'})
            except Wallet.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Wallet not found'})
        
        elif action == 'link_wallet':
            wallet_id = request.POST.get('wallet_id')
            try:
                wallet = Wallet.objects.get(wallet_id=wallet_id, user_id__isnull=True)
                wallet.user_id = user
                wallet.save()
                return JsonResponse({'success': True, 'message': 'Wallet linked successfully'})
            except Wallet.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Wallet not found or already linked'})
    
    normal_wallet = Wallet.objects.filter(user_id=user, wallet_type='Other').first()
    avs_wallets = Wallet.objects.filter(wallet_type='AVS').order_by('-created_at')
    linked_wallets = avs_wallets.filter(user_id=user)
    unlinked_wallets = avs_wallets.filter(user_id__isnull=True)
    transactions = Payment.objects.filter(Q(payment_mode='Wallet', reference_order__created_by=username) | Q(payment_mode='Wallet', refund_for=username)).order_by('-created_at')
    
    # Calculate total AVS wallet amount
    avs_total = sum(wallet.wallet_amount for wallet in linked_wallets)
    
    return render(request, 'customer/wallet.html', {
        'normal_wallet': normal_wallet,
        'linked_wallets': linked_wallets,
        'unlinked_wallets': unlinked_wallets,
        'transactions': transactions,
        'avs_total': avs_total,
        'user': user
    })

def payment_history(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    from management.models import Payment, Wallet
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    orders = Order.objects.filter(created_by=username).exclude(payment_status='Pending').order_by('-created_at')
    payments = Payment.objects.filter(Q(reference_order__created_by=username) | Q(refund_for=username)).order_by('-created_at')
    linked_wallets = Wallet.objects.filter(user_id=user, wallet_type='AVS')
    
    return render(request, 'customer/payment_history.html', {'orders': orders, 'payments': payments, 'user': user, 'linked_wallets': linked_wallets})


def download_invoice(request, order_id):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    import json
    
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    order = get_object_or_404(Order, order_id=order_id)
    if order.order_status != 'Delivered':
        return redirect('order_history')
    items = json.loads(order.items_details) if order.items_details else []
    gstin = GSTDetail.objects.filter(business_code=order.sold_by).order_by('-created_at')

    calc_total = lambda key: sum(item[key] * item['quantity'] for item in items)
    total = {
    'total_items': sum(item['quantity'] for item in items),
    'total_mrp': calc_total('mrp'),
    'total_base_price': calc_total('base_price'),
    'total_price': calc_total('price'),
    'total_igst': sum(item['base_price']*item['quantity']*item['gst']/100 for item in items),
    'total_discount': calc_total('mrp')-calc_total('price')
    }

    return render(request, 'customer/invoice.html', {'order': order, 'items': items,'gstin':gstin,'total':total})


def get_delivery_data(request):
    from django.http import JsonResponse
    import json
    pin = request.GET.get('pin', '')
    business = BusinessDetail.objects.first()
    delivery_settings, _ = DeliverySettings.objects.get_or_create(business_code=business)
    delivery_zone = DeliveryZone.objects.filter(business_code=business, pincode_to=pin, status='Active').first()
    return JsonResponse({
        'min_amount_free_delivery': float(delivery_settings.min_amount_free_delivery or 0),
        'base_charge': float(delivery_zone.base_charge) if delivery_zone else 0,
        'max_distance_km': float(delivery_settings.max_distance_km or 0),
        'delivery_free': delivery_settings.delivery_free,
        'ship_free': delivery_settings.ship_free,
    })

def update_address(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    if request.method == 'POST':
        from customer.models import SavedAddress
        from django.http import JsonResponse
        
        addr_id = request.POST.get('address_id')
        if addr_id:
            SavedAddress.objects.filter(id=addr_id).update(
                name=request.POST.get('name'),
                phone=request.POST.get('phone'),
                address1=request.POST.get('address1'),
                address2=request.POST.get('address2'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                pin=request.POST.get('pin'),
                country=request.POST.get('country')
            )
            return JsonResponse({'success': True})
        return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def set_default_address(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')

    if request.method == 'POST':
        from customer.models import SavedAddress, Customer
        from django.http import JsonResponse
        
        addr_id = request.POST.get('address_id')
        if addr_id:
            address = SavedAddress.objects.get(id=addr_id)
            username = request.session.get('user_id')
            customer = Customer.objects.get(username=username)
            
            SavedAddress.objects.filter(customer=customer, address_type=address.address_type).update(is_default=False)
            address.is_default = True
            address.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False})
    return JsonResponse({'success': False})


def delete_address(request, address_id):
    from django.http import JsonResponse
    if not request.session.get('is_logged_in'):
        return JsonResponse({'success': False})
    try:
        address = SavedAddress.objects.get(id=address_id)
        address.delete()
        return JsonResponse({'success': True})
    except SavedAddress.DoesNotExist:
        return JsonResponse({'success': False})

def edit_address(request, address_id):
    from django.http import JsonResponse
    if not request.session.get('is_logged_in'):
        return JsonResponse({'success': False})
    if request.method == 'POST':
        try:
            address = SavedAddress.objects.get(id=address_id)
            address.name = request.POST.get('name')
            address.phone = request.POST.get('phone')
            address.address1 = request.POST.get('address1')
            address.address2 = request.POST.get('address2')
            address.city = request.POST.get('city')
            address.state = request.POST.get('state')
            address.pin = request.POST.get('pin')
            address.country = request.POST.get('country')
            address.save()
            return JsonResponse({'success': True})
        except SavedAddress.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})
