from django.shortcuts import render, redirect, get_object_or_404
from business.models import Product, ProductCategory, Order, Staff, BusinessDetail, ProductImage, StaffUser
from users.models import Customer

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
            placed_at=timezone.now()
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
        
        payment_method = request.POST.get('payment_method')
        cart_data = json.loads(order_data['cart_data'])
        
        # Enrich cart data with product details
        enriched_items = []
        for item in cart_data.values():
            try:
                product = Product.objects.get(id=item['id'])
                enriched_items.append({
                    'id': item['id'],
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': float(item['price']),
                    'mrp': float(product.mrp),
                    'base_price': float(product.base_price),
                    'gst': float(product.gst)
                })
            except Product.DoesNotExist:
                enriched_items.append(item)
        
        # Generate order ID
        order_id = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
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
            total_amount=order_data['total_amount'],
            sold_by='B001',
            payment_method=payment_method,
            payment_status='Pending',
            placed_type='Online',
            placed_at=timezone.now(),
            order_status='Placed',
            created_by=request.session.get('user_id'),
            comments=json.dumps(enriched_items)
        )
        
        # Clear session data
        del request.session['order_data']
        
        return render(request, 'shop/order_success.html', {'order': order, 'user': user})
    
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
        
        # Enrich cart data with product details
        enriched_items = []
        for item in cart_data.values():
            try:
                product = Product.objects.get(id=item['id'])
                enriched_items.append({
                    'id': item['id'],
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': float(item['price']),
                    'mrp': float(product.mrp),
                    'base_price': float(product.base_price),
                    'gst': float(product.gst)
                })
            except Product.DoesNotExist:
                enriched_items.append(item)
        
        order_id = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Set order status based on payment success
        order_status = 'Confirmed'
        confirmed_at = timezone.now()
        confirmed_by = username
        
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
            total_amount=order_data['total_amount'],
            sold_by='B001',
            payment_method=payment_method,
            payment_status='Successful',
            placed_type='Online',
            placed_at=timezone.now(),
            order_status=order_status,
            confirmed_at=confirmed_at,
            confirmed_by=confirmed_by,
            created_by=username,
            comments=json.dumps(enriched_items)
        )
        
        # Create payment record
        from business.models import Payment
        transaction_id = f"TXN{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
        Payment.objects.create(
            transaction_id=transaction_id,
            amount=order_data['total_amount'],
            status='Successful',
            payment_mode=payment_method,
            transaction_type='Debit',
            reference_order=order,
            created_by=username
        )
        
        del request.session['order_data']
        return render(request, 'shop/order_success.html', {'order': order, 'user': user})
    
    # Load saved payment methods
    from users.models import Customer, SavedPaymentMethod
    username = request.session.get('user_id')
    try:
        customer = Customer.objects.get(username=username)
        user = customer
        saved_card = SavedPaymentMethod.objects.filter(customer=customer, payment_type='Card', is_default=True).first()
        saved_upi = SavedPaymentMethod.objects.filter(customer=customer, payment_type='UPI', is_default=True).first()
    except Customer.DoesNotExist:
        return redirect('login')
    
    return render(request, 'shop/process_payment.html', {
        'order_data': order_data,
        'saved_card': saved_card,
        'saved_upi': saved_upi,
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
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    business_code = request.session.get('business_code')
    products = Product.objects.filter(business_code=business_code)
    orders = Order.objects.filter(sold_by=business_code)
    staff_count = Staff.objects.filter(business_code=business_code).count()
    
    return render(request, 'shop/seller_dashboard.html', {
        'products': products,
        'orders': orders,
        'staff_count': staff_count,
        'business_code': business_code
    })

def add_product(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    if request.method == 'POST':
        business_code = request.session.get('business_code')
        business = BusinessDetail.objects.get(code=business_code)
        
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
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
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
        
        return redirect('seller_dashboard')
    
    categories = ProductCategory.objects.all()
    return render(request, 'shop/edit_product.html', {'product': product, 'categories': categories})

def manage_orders(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'shop/manage_orders.html', {'orders': orders})

def manage_staff(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    business_code = request.session.get('business_code', 'B001')
    staff_list = Staff.objects.filter(business_code=business_code)
    return render(request, 'shop/manage_staff.html', {
        'staff_list': staff_list,
        'business_code': business_code
    })

def add_staff(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    business_code = request.session.get('business_code', 'B001')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        user, created = StaffUser.objects.get_or_create(
            username=username,
            defaults={
                'first_name': request.POST.get('first_name'),
                'middle_name': request.POST.get('middle_name'),
                'last_name': request.POST.get('last_name'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone'),
                'password': 'default123'
            }
        )
        
        Staff.objects.create(
            username=user,
            staff_id=request.POST.get('staff_id'),
            business_code_id=business_code,
            staff_role=request.POST.get('staff_role'),
            phone=request.POST.get('phone'),
            created_by='admin'
        )
        return redirect('manage_staff')
    
    return render(request, 'shop/add_staff.html', {'business_code': business_code})

def management_dashboard(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
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
    
    from business.models import Payment
    username = request.session.get('user_id')
    user = Customer.objects.filter(username=username).first()
    orders = Order.objects.filter(created_by=username).exclude(payment_status='Pending').order_by('-created_at')
    payments = Payment.objects.filter(reference_order__created_by=username).order_by('-created_at')
    
    return render(request, 'shop/payment_history.html', {'orders': orders, 'payments': payments, 'user': user})

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
