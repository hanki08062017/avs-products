from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from business.models import Product, ProductCategory, Order, Staff, BusinessDetail, ProductImage, StaffUser
from users.models import Customer
from django.db import models

def home(request):
    from django.db.models import Q
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
    
    return render(request, 'shop/home.html', {
        'products': products,
        'categories': categories,
        'products_by_category': dict(products_by_category),
        'search_query': search_query,
        'user': user
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})

def checkout(request):
    if not request.session.get('is_logged_in'):
        request.session['next'] = '/checkout/'
        return redirect('login')
    
    # Get user
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    
    if request.method == 'POST':
        import json
        from django.utils import timezone
        
        cart_data = json.loads(request.POST.get('cart_data'))
        total_amount = request.POST.get('total_amount')
        
        # Generate order ID
        order_id = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create order
        order = Order.objects.create(
            order_id=order_id,
            customer_name=request.POST.get('customer_name'),
            customer_email=request.POST.get('customer_email'),
            customer_phone=request.POST.get('customer_phone'),
            bill_address=request.POST.get('bill_address'),
            ship_address=request.POST.get('ship_address'),
            total_amount=total_amount,
            sold_by='B001',  # Default business code
            payment_method=request.POST.get('payment_method'),
            placed_type='Online',
            placed_at=timezone.now(),
            placed_by=username
        )
        
        return render(request, 'shop/order_success.html', {'order': order})
    
    return render(request, 'shop/checkout.html', {'user': user})

def place_order(request):
    if not request.session.get('is_logged_in'):
        request.session['next'] = '/place-order/'
        return redirect('login')
    
    if request.method == 'POST':
        from users.models import Customer, SavedAddress
        
        username = request.session.get('user_id')
        customer = Customer.objects.get(username=username)
        
        # Handle billing address
        if request.POST.get('is_new_billing') == 'true':
            billing_count = SavedAddress.objects.filter(customer=customer, address_type='Billing').count()
            if billing_count >= 5:
                oldest = SavedAddress.objects.filter(customer=customer, address_type='Billing').order_by('created_at').first()
                if oldest:
                    oldest.delete()
            
            SavedAddress.objects.create(
                customer=customer,
                address_type='Billing',
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
                SavedAddress.objects.filter(id=bill_addr_id).update(
                    name=request.POST.get('bill_name'),
                    phone=request.POST.get('bill_phone'),
                    address1=request.POST.get('bill_address1'),
                    address2=request.POST.get('bill_address2'),
                    city=request.POST.get('bill_city'),
                    state=request.POST.get('bill_state'),
                    pin=request.POST.get('bill_pin'),
                    country=request.POST.get('bill_country')
                )
        
        # Handle shipping address
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
    from users.models import Customer, SavedAddress
    username = request.session.get('user_id')
    customer = Customer.objects.get(username=username)
    user = customer
    
    billing_addresses = SavedAddress.objects.filter(customer=customer, address_type__in=['Billing', 'Both']).order_by('-is_default', '-created_at')[:5]
    shipping_addresses = SavedAddress.objects.filter(customer=customer, address_type__in=['Shipping', 'Both']).order_by('-is_default', '-created_at')[:5]
    
    return render(request, 'shop/place_order.html', {
        'billing_addresses': billing_addresses,
        'shipping_addresses': shipping_addresses,
        'customer': customer,
        'user': user
    })

def update_address(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    if request.method == 'POST':
        from users.models import SavedAddress
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
        from users.models import SavedAddress, Customer
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
        cart_data = json.loads(order_data['cart_data'])
        
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
                    seller_code = first_business.code if first_business else 'B001'
                items_by_seller[seller_code].append({
                    'id': item['id'],
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': float(item['price']),
                    'mrp': float(product.mrp),
                    'base_price': float(product.base_price),
                    'gst': float(product.gst)
                })
            except Product.DoesNotExist:
                # Use first business code as fallback
                first_business = BusinessDetail.objects.first()
                seller_code = first_business.code if first_business else 'B001'
                items_by_seller[seller_code].append(item)
        
        # Create separate order for each seller
        created_orders = []
        for seller_code, items in items_by_seller.items():
            # Calculate total for this seller's items
            seller_total = sum(item['price'] * item['quantity'] for item in items)
            
            # Generate unique order ID for each seller
            order_id = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
            
            # Create order with Placed status and Pending payment for COD
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
                sold_by=seller_code,
                payment_method=payment_method,
                payment_status='Pending',
                placed_type='Online',
                placed_at=timezone.now(),
                placed_by=request.session.get('user_id'),
                order_status='Placed',
                created_by=request.session.get('user_id'),
                comments=json.dumps(items)
            )
            
            # Reduce stock for each item
            for item in items:
                try:
                    product = Product.objects.get(id=item['id'])
                    product.stock -= item['quantity']
                    product.save()
                except Product.DoesNotExist:
                    pass
            
            created_orders.append(order)
        
        # Clear session data
        del request.session['order_data']
        
        return render(request, 'shop/order_success.html', {'orders': created_orders, 'user': user})
    
    return render(request, 'shop/confirm_order.html', {'order_data': order_data, 'user': user})

def process_payment(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    order_data = request.session.get('order_data')
    if not order_data:
        return redirect('confirm_order')
    
    if request.method == 'POST':
        from django.utils import timezone
        from users.models import Customer, SavedPaymentMethod
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
        
        cart_data = json.loads(order_data['cart_data'])
        avs_wallet_id = request.POST.get('avs_wallet_id', '')
        
        # Verify OTP for AVS wallet payment
        if payment_method == 'Wallet' and avs_wallet_id:
            from business.models import Wallet as WalletModel
            wallet = WalletModel.objects.filter(wallet_id=avs_wallet_id).first()
            if wallet and wallet.wallet_type == 'AVS':
                # Check if OTP was verified
                if not request.session.get(f'payment_verified_{avs_wallet_id}'):
                    return render(request, 'shop/process_payment.html', {
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
                    seller_code = first_business.code if first_business else 'B001'
                items_by_seller[seller_code].append({
                    'id': item['id'],
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': float(item['price']),
                    'mrp': float(product.mrp),
                    'base_price': float(product.base_price),
                    'gst': float(product.gst)
                })
            except Product.DoesNotExist:
                # Use first business code as fallback
                first_business = BusinessDetail.objects.first()
                seller_code = first_business.code if first_business else 'B001'
                items_by_seller[seller_code].append(item)
        
        # Create separate order for each seller
        created_orders = []
        for seller_code, items in items_by_seller.items():
            # Calculate total for this seller's items
            seller_total = sum(item['price'] * item['quantity'] for item in items)
            
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
                sold_by=seller_code,
                payment_method=payment_method,
                payment_status='Successful',
                placed_type='Online',
                placed_at=timezone.now(),
                order_status='Confirmed',
                confirmed_at=timezone.now(),
                confirmed_by='System',
                created_by=username,
                comments=json.dumps(items)
            )
            
            # Create payment record for each order
            from business.models import Payment
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
            if payment_method == 'Wallet' and avs_wallet_id:
                from business.models import Wallet as WalletModel
                from decimal import Decimal
                wallet = WalletModel.objects.filter(wallet_id=avs_wallet_id).first()
                if wallet:
                    seller_total_decimal = Decimal(str(seller_total))
                    if wallet.wallet_amount >= seller_total_decimal:
                        wallet.wallet_amount -= seller_total_decimal
                        wallet.modified_by = username
                        wallet.save()
                    else:
                        # Insufficient balance - should not happen if frontend validates
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
        return render(request, 'shop/order_success.html', {'orders': created_orders, 'user': user})
    
    # Load saved payment methods
    from users.models import Customer, SavedPaymentMethod
    from business.models import Wallet
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
    
    return render(request, 'shop/process_payment.html', {
        'order_data': order_data,
        'saved_card': saved_card,
        'saved_upi': saved_upi,
        'normal_wallet': normal_wallet,
        'avs_wallets': avs_wallets,
        'user': user
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        business_code = request.POST.get('business_code')
        
        try:
            user = StaffUser.objects.get(username=username)
            if not business_code:
                return render(request, 'shop/staff_login.html', {'error': 'Business code is required for staff login'})
            
            staff = Staff.objects.get(username=user, business_code=business_code)
            
            # Check if staff status is Active
            if staff.status != 'Active':
                return render(request, 'shop/staff_login.html', {'error': 'Your account is not active. Please contact administrator.'})
            
            request.session['user_id'] = username
            request.session['is_logged_in'] = True
            request.session['user_type'] = 'staff'
            request.session['business_code'] = business_code
            return redirect('seller_dashboard')
        except (StaffUser.DoesNotExist, Staff.DoesNotExist):
            return render(request, 'shop/staff_login.html', {'error': 'Invalid credentials or business code'})
    
    return render(request, 'shop/staff_login.html')

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
            return render(request, 'shop/customer_login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'shop/customer_login.html')
    
    return render(request, 'shop/login.html')

def logout_view(request):
    user_type = request.session.get('user_type')
    request.session.flush()
    if user_type == 'staff':
        return redirect('staff_login')
    return redirect('home')

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
            return render(request, 'shop/signup.html', {'error': 'Passwords do not match'})
        
        try:
            if Customer.objects.filter(username=username).exists():
                return render(request, 'shop/signup.html', {'error': 'Username already exists'})
            
            if Customer.objects.filter(email=email).exists():
                return render(request, 'shop/signup.html', {'error': 'Email already exists'})
            
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
            return render(request, 'shop/signup.html', {'error': str(e)})
    
    return render(request, 'shop/signup.html')

def profile_view(request, username):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    session_username = request.session.get('user_id')
    if session_username != username:
        return redirect('home')
    
    user_type = request.session.get('user_type')
    
    try:
        if user_type == 'staff':
            user = StaffUser.objects.get(username=username)
            profile = user.profile
            business_code = request.session.get('business_code')
            staff = Staff.objects.get(username=user, business_code=business_code)
            
            if request.method == 'POST':
                user.first_name = request.POST.get('first_name')
                user.middle_name = request.POST.get('middle_name')
                user.last_name = request.POST.get('last_name')
                user.email = request.POST.get('email')
                user.phone = request.POST.get('phone')
                user.save()
                
                profile.address1 = request.POST.get('address1')
                profile.address2 = request.POST.get('address2')
                profile.city = request.POST.get('city')
                profile.state = request.POST.get('state')
                profile.pin = request.POST.get('pin')
                profile.country = request.POST.get('country')
                profile.phone1 = request.POST.get('phone1')
                profile.phone2 = request.POST.get('phone2')
                profile.save()
                
                return render(request, 'shop/profile.html', {'user': user, 'profile': profile, 'staff': staff, 'success': 'Profile updated successfully'})
            
            return render(request, 'shop/profile.html', {'user': user, 'profile': profile, 'staff': staff})
        else:
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
            
            from users.models import SavedAddress
            billing_addresses = SavedAddress.objects.filter(customer=user, address_type__in=['Billing', 'Both']).order_by('-is_default', '-created_at')
            shipping_addresses = SavedAddress.objects.filter(customer=user, address_type__in=['Shipping', 'Both']).order_by('-is_default', '-created_at')
            
            success = request.session.pop('profile_success', None)
            return render(request, 'shop/customer_profile.html', {
                'user': user, 
                'profile': profile, 
                'success': success,
                'billing_addresses': billing_addresses,
                'shipping_addresses': shipping_addresses
            })
    except (StaffUser.DoesNotExist, Customer.DoesNotExist):
        return redirect('login')

def seller_dashboard(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    from business.models import Payment, StaffPrivileges
    from django.core.paginator import Paginator
    
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
    
    return render(request, 'shop/seller_dashboard.html', {
        'products': products,
        'orders': orders,
        'staff_count': staff_count,
        'staff_list': staff_list,
        'payments': payments,
        'business_code': business_code,
        'privileges': privileges,
        'is_admin': is_admin,
        'view_type': view_type,
        'total_count': paginator.count
    })

def add_product(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    if request.method == 'POST':
        business_code = request.session.get('business_code')
        business = BusinessDetail.objects.get(code=business_code)
        
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
                            cost_price=row['cost_price'],
                            selling_price=row['selling_price'],
                            stock=row['stock'],
                            source=row.get('source', ''),
                            manufacturer=row.get('manufacturer', ''),
                            business_code_id=business_code,
                            created_by='admin',
                            added_by=business.business_name
                        )
                        success_count += 1
                    except Exception as e:
                        errors.append(f"Row {index+2}: {str(e)}")
                
                if errors:
                    return render(request, 'shop/add_product.html', {
                        'categories': ProductCategory.objects.all(),
                        'success': f'{success_count} products added successfully',
                        'errors': errors
                    })
                return redirect('seller_dashboard')
            except Exception as e:
                return render(request, 'shop/add_product.html', {
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
            cost_price=request.POST.get('cost_price'),
            selling_price=request.POST.get('selling_price'),
            stock=request.POST.get('stock'),
            source=request.POST.get('source'),
            manufacturer=request.POST.get('manufacturer'),
            business_code_id=business_code,
            created_by='admin',
            added_by=business.business_name
        )
        
        images = request.FILES.getlist('images')
        for idx, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(idx == 0)
            )
        
        return redirect('seller_dashboard')
    
    categories = ProductCategory.objects.all()
    return render(request, 'shop/add_product.html', {'categories': categories})

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
        product.cost_price = request.POST.get('cost_price')
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
    return render(request, 'shop/edit_product.html', {'product': product, 'categories': categories})

def view_product(request, product_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    product = Product.objects.get(id=product_id)
    return render(request, 'shop/view_product.html', {'product': product})

def manage_orders(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    business_code = request.session.get('business_code')
    orders = Order.objects.filter(sold_by=business_code).order_by('-created_at')
    print(f"DEBUG: business_code={business_code}, orders_count={orders.count()}")
    return render(request, 'shop/manage_orders.html', {'orders': orders, 'business_code': business_code})

def update_order_status(request, order_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    if request.method == 'POST':
        import json
        from django.utils import timezone
        
        data = json.loads(request.body)
        new_status = data.get('status')
        comments = data.get('comments', '')
        
        username = request.session.get('user_id')
        user = StaffUser.objects.get(username=username)
        modifier_name = f"{user.first_name} {user.last_name}"
        
        order = Order.objects.get(order_id=order_id)
        order.order_status = new_status
        order.comments = comments
        order.modified_by = modifier_name
        order.modified_at = timezone.now()
        
        if new_status == 'Confirmed':
            order.confirmed_at = timezone.now()
            order.confirmed_by = modifier_name
        elif new_status == 'Processing':
            order.processing_at = timezone.now()
            order.processing_by = modifier_name
        elif new_status == 'Shipped':
            order.shipped_at = timezone.now()
            order.shipped_by = modifier_name
        elif new_status == 'Delivered':
            order.delivered_at = timezone.now()
            order.delivered_by = modifier_name
        elif new_status == 'Cancelled':
            order.cancelled_at = timezone.now()
            order.cancelled_by = modifier_name
        
        order.save()
        return JsonResponse({'success': True})
    
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
    items = json.loads(order.comments) if order.comments else []
    
    return render(request, 'shop/order_details.html', {'order': order, 'items': items})

def manage_staff(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    business_code = request.session.get('business_code', 'B001')
    staff_list = Staff.objects.filter(business_code=business_code)
    return render(request, 'shop/manage_staff.html', {
        'staff_list': staff_list,
        'business_code': business_code
    })

def add_staff(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    business_code = request.session.get('business_code', 'B001')
    username = request.session.get('user_id')
    
    # Get business details for symbol and type
    business = BusinessDetail.objects.get(code=business_code)
    
    # Determine staff role based on business type
    if business.business_type == 'Seller':
        allowed_role = 'Seller-Staff'
    elif business.business_type == 'Shop':
        allowed_role = 'Shop-Staff'
    else:
        allowed_role = 'Seller-Staff'  # Default
    
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
        from business.models import StaffPrivileges
        staff_role = request.POST.get('staff_role')
        
        username_new = request.POST.get('username')
        user, created = StaffUser.objects.get_or_create(
            username=username_new,
            defaults={
                'first_name': request.POST.get('first_name'),
                'middle_name': request.POST.get('middle_name'),
                'last_name': request.POST.get('last_name'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone'),
                'password': 'default123'
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
        profile.save()
        
        staff = Staff.objects.create(
            username=user,
            staff_id=request.POST.get('staff_id'),
            business_code_id=business_code,
            staff_role=staff_role,
            phone=request.POST.get('phone'),
            created_by=username
        )
        
        # Create privileges for staff - Seller-Admin gets all privileges by default
        if staff_role == 'Seller-Admin':
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
        
        return redirect('manage_staff')
    
    return render(request, 'shop/add_staff.html', {
        'business_code': business_code,
        'allowed_role': allowed_role,
        'auto_staff_id': auto_staff_id,
        'business_type': business.business_type
    })

def view_staff(request, staff_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    from business.models import StaffPrivileges
    business_code = request.session.get('business_code')
    staff = get_object_or_404(Staff, staff_id=staff_id, business_code=business_code)
    privileges = StaffPrivileges.objects.filter(staff=staff).first()
    
    return render(request, 'shop/view_staff.html', {
        'staff': staff,
        'privileges': privileges,
        'business_code': business_code
    })

def edit_staff(request, staff_id):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    from business.models import StaffPrivileges
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
        staff.staff_role = request.POST.get('staff_role')
        
        # Admin cannot change own status
        if not (is_editing_self and staff.staff_role in ['Seller-Admin', 'Shop-Admin']):
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
        profile.save()
        
        # Update privileges - Seller-Admin always has all privileges
        if staff.staff_role == 'Seller-Admin':
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
    
    return render(request, 'shop/edit_staff.html', {
        'staff': staff,
        'privileges': privileges,
        'business_code': business_code
    })

def management_dashboard(request):
    if not request.session.get('is_logged_in') or request.session.get('user_type') != 'staff':
        return redirect('staff_login')
    
    total_users = StaffUser.objects.count() + Customer.objects.count()
    total_businesses = BusinessDetail.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_staff = Staff.objects.count()
    
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    businesses = BusinessDetail.objects.all()
    
    return render(request, 'shop/management_dashboard.html', {
        'total_users': total_users,
        'total_businesses': total_businesses,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_staff': total_staff,
        'recent_orders': recent_orders,
        'businesses': businesses
    })

def order_history(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    orders = Order.objects.filter(created_by=username).order_by('-created_at')
    
    return render(request, 'shop/order_history.html', {'orders': orders, 'user': user})

def payment_history(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    from business.models import Payment, Wallet
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    orders = Order.objects.filter(created_by=username).exclude(payment_status='Pending').order_by('-created_at')
    payments = Payment.objects.filter(reference_order__created_by=username).order_by('-created_at')
    linked_wallets = Wallet.objects.filter(user_id=user, wallet_type='AVS')
    
    return render(request, 'shop/payment_history.html', {'orders': orders, 'payments': payments, 'user': user, 'linked_wallets': linked_wallets})

def wallet_view(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    from business.models import Wallet, Payment
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
    transactions = Payment.objects.filter(payment_mode='Wallet', reference_order__created_by=username).order_by('-created_at')
    
    # Calculate total AVS wallet amount
    avs_total = sum(wallet.wallet_amount for wallet in linked_wallets)
    
    return render(request, 'shop/wallet.html', {
        'normal_wallet': normal_wallet,
        'linked_wallets': linked_wallets,
        'unlinked_wallets': unlinked_wallets,
        'transactions': transactions,
        'avs_total': avs_total,
        'user': user
    })

def download_invoice(request, order_id):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    import json
    
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    order = get_object_or_404(Order, order_id=order_id)
    items = json.loads(order.comments) if order.comments else []
    
    return render(request, 'shop/invoice.html', {'order': order, 'items': items})

def delete_address(request, address_id):
    from users.models import SavedAddress
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
    from users.models import SavedAddress
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
