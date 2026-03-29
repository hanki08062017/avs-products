import os
from django.db import models
from customer.models import Customer
from django.db.models import Sum, Q, Case, When, DecimalField

def _product_image_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    product = instance.product
    seller_code = product.business_code.code if product.business_code else 'unknown'
    product_slug = f"{product.id}_{product.product_name.strip().replace(' ', '_').lower()}"
    existing_count = product.images.count()
    seq = existing_count + 1
    return f"product/{seller_code}/{product_slug}_{seq}{ext}"

class BusinessDetail(models.Model):
    class Meta:
        db_table = 'business_businessdetail'

    BUSINESS_TYPE_CHOICES = [
        ('Seller', 'Seller'),
        ('Shop', 'Shop'),
        ('Retailer', 'Retailer'),
        ('Service', 'Service'),
        ('Management', 'Management'),
    ]
    
    MODE_CHOICES = [
        ('Offline', 'Offline'),
        ('Online', 'Online'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    serial_no = models.AutoField(primary_key=True)
    business_name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    business_type = models.CharField(max_length=100, choices=BUSINESS_TYPE_CHOICES)
    symbol = models.CharField(max_length=50)
    mode = models.CharField(max_length=100, choices=MODE_CHOICES)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    def __str__(self):
        return f"{self.business_name} ({self.code})"

class GSTDetail(models.Model):
    class Meta:
        db_table = 'business_gstdetail'

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    serial_no = models.AutoField(primary_key=True)
    gst_number = models.CharField(max_length=15, unique=True)
    pan = models.CharField(max_length=10)
    reg_date = models.DateField()
    valid_till = models.DateField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    pin = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    business_code = models.ForeignKey(BusinessDetail, to_field='code', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    def __str__(self):
        return f"GST: {self.gst_number}"


class ProductCategory(models.Model):
    class Meta:
        db_table = 'business_productcategory'

    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100)
    hsn = models.CharField(max_length=50)
    sgst = models.DecimalField(max_digits=5, decimal_places=2)
    cgst = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
    @property
    def gst(self):
        return self.sgst + self.cgst
    
    def __str__(self):
        return f"{self.category} - {self.sub_category}"

class Product(models.Model):
    class Meta:
        db_table = 'business_product'

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    product_name = models.CharField(max_length=255)
    description = models.TextField()
    product_category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=50)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    ship_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    source = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    business_code = models.ForeignKey(BusinessDetail, to_field='code', on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.CharField(max_length=100)
    added_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    modified_at = models.DateTimeField(blank=True, null=True)
    
    @property
    def category(self):
        return self.product_category.category
    
    @property
    def sub_category(self):
        return self.product_category.sub_category
    
    @property
    def gst(self):
        return self.product_category.gst
    
    @property
    def base_price(self):
        return round(self.selling_price / (1 + (self.gst / 100)), 2)
    
    @property
    def discount_percentage(self):
        if self.mrp > self.selling_price:
            return round(((self.mrp - self.selling_price) / self.mrp) * 100)
        return 0
    
    @property
    def unit_abbr(self):
        try:
            unit_obj = UnitOfMeasurement.objects.get(name__iexact=self.unit)
            return unit_obj.abbreviation
        except UnitOfMeasurement.DoesNotExist:
            return self.unit
    
    def save(self, *args, **kwargs):
        if not self.id:
            prefix = '_'.join(self.product_name.strip().lower().split())
            existing = Product.objects.filter(id__startswith=prefix).values_list('id', flat=True)
            nums = []
            for pid in existing:
                try:
                    nums.append(int(str(pid)[len(prefix):]))
                except ValueError:
                    pass
            num = max(nums) + 1 if nums else 1
            self.id = f'{prefix}{num}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=_product_image_path)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_image'
    
    def __str__(self):
        return f"{self.product.product_name} - Image"

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Placed', 'Placed'),
        ('Confirmed', 'Confirmed'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('Wallet', 'Wallet'),
        ('Cash', 'Cash'),
        ('COD', 'COD'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PLACED_TYPE_CHOICES = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('New', 'New'),
        ('Return', 'Return'),
        ('Exchange', 'Exchange'),
        ('Cancel', 'Cancel'),
    ]
    
    order_id = models.CharField(max_length=50, primary_key=True)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    bill_name = models.CharField(max_length=255)
    bill_phone = models.CharField(max_length=20)
    bill_address1 = models.CharField(max_length=255)
    bill_address2 = models.CharField(max_length=255, blank=True, null=True)
    bill_city = models.CharField(max_length=100)
    bill_state = models.CharField(max_length=100)
    bill_pin = models.CharField(max_length=10)
    bill_country = models.CharField(max_length=100, default='India')
    ship_name = models.CharField(max_length=255)
    ship_phone = models.CharField(max_length=20)
    ship_address1 = models.CharField(max_length=255)
    ship_address2 = models.CharField(max_length=255, blank=True, null=True)
    ship_city = models.CharField(max_length=100)
    ship_state = models.CharField(max_length=100)
    ship_pin = models.CharField(max_length=10)
    ship_country = models.CharField(max_length=100, default='India')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sold_by = models.CharField(max_length=100)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Placed')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    placed_type = models.CharField(max_length=20, choices=PLACED_TYPE_CHOICES)
    old_order_id = models.CharField(max_length=50, blank=True, null=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='New')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    items_details = models.TextField(blank=True, null=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    placed_by = models.CharField(max_length=100, blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    confirmed_by = models.CharField(max_length=100, blank=True, null=True)
    confirmed_comments = models.TextField(blank=True, null=True)
    processing_at = models.DateTimeField(blank=True, null=True)
    processing_by = models.CharField(max_length=100, blank=True, null=True)
    processing_comments = models.TextField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    shipped_by = models.CharField(max_length=100, blank=True, null=True)
    shipped_comments = models.TextField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    delivered_by = models.CharField(max_length=100, blank=True, null=True)
    delivered_comments = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancelled_by = models.CharField(max_length=100, blank=True, null=True)
    cancelled_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    modified_comments = models.TextField(blank=True, null=True)
    invoice_no = models.IntegerField(unique=True, null=True, blank=True)
    
    class Meta:
        db_table = 'business_order'
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        
        # Handle initial order creation
        if not self.pk:
            # Always set placed_at and placed_by for new orders
            if not self.placed_at:
                self.placed_at = timezone.now()
            if not self.placed_by:
                self.placed_by = self.customer_name
            
            # Auto-confirm if payment is successful on creation
            if self.payment_status == 'Successful':
                self.order_status = 'Confirmed'
                self.confirmed_at = timezone.now()
                self.confirmed_by = 'System'
        
        # Handle status and payment changes for existing orders
        if self.pk:
            try:
                old_order = Order.objects.get(pk=self.pk)
                
                # Auto-confirm when payment becomes successful
                if old_order.payment_status != 'Successful' and self.payment_status == 'Successful':
                    if self.order_status == 'Placed':
                        self.order_status = 'Confirmed'
                        self.confirmed_at = timezone.now()
                        self.confirmed_by = 'System'
                
                # Handle manual status changes
                if old_order.order_status != self.order_status:
                    status_map = {
                        'Placed': ('placed_at', 'placed_by'),
                        'Confirmed': ('confirmed_at', 'confirmed_by'),
                        'Processing': ('processing_at', 'processing_by'),
                        'Shipped': ('shipped_at', 'shipped_by'),
                        'Delivered': ('delivered_at', 'delivered_by'),
                        'Cancelled': ('cancelled_at', 'cancelled_by'),
                    }
                    if self.order_status in status_map:
                        time_field, user_field = status_map[self.order_status]
                        if not getattr(self, time_field):
                            setattr(self, time_field, timezone.now())
                        if not getattr(self, user_field) and self.modified_by:
                            setattr(self, user_field, self.modified_by)
            except Order.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"
    

class Payment(models.Model):
    class Meta:
        db_table = 'business_payment'

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
        ('Wallet', 'Wallet'),
    ]
    
    TRANSACTION_TYPE_CHOICES = [
        ('Credit', 'Credit'),
        ('Debit', 'Debit'),
        ('Refund', 'Refund'),
        ('Cashback', 'Cashback'),
    ]
    
    id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODE_CHOICES)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    reference_order = models.ForeignKey(Order, to_field='order_id', on_delete=models.CASCADE)
    avs_wallet_id = models.CharField(max_length=50, blank=True, null=True)
    refund_for = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    processing_at = models.DateTimeField(blank=True, null=True)
    processing_by = models.CharField(max_length=100, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} - ₹{self.amount}"

class UnitOfMeasurement(models.Model):
    class Meta:
        db_table = 'business_unitofmeasurement'

    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Wallet(models.Model):
    class Meta:
        db_table = 'business_wallet'

    WALLET_TYPE_CHOICES = [
        ('AVS', 'AVS'),
        ('Other', 'Other'),        
    ]
    
    wallet_id = models.CharField(max_length=50, primary_key=True, editable=False)
    user_id = models.ForeignKey(Customer, to_field='username', on_delete=models.CASCADE, blank=True, null=True)
    wallet_type = models.CharField(max_length=50, choices=WALLET_TYPE_CHOICES)
    customer_name = models.CharField(max_length=255)
    customer_id = models.CharField(max_length=50, unique=True)
    customer_mobile = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.wallet_id:
            last = Wallet.objects.order_by('-created_at').values_list('wallet_id', flat=True).first()
            if last:
                try:
                    num = int(last.replace('wallet', '')) + 1
                except ValueError:
                    num = Wallet.objects.count() + 1
            else:
                num = 1
            self.wallet_id = f'wallet{num}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - Wallet ({self.wallet_id})"
    
    @property
    def wallet_amount(self):
        transactions = WalletTransaction.objects.filter(avs_customer_id=self.customer_id)
        result = transactions.aggregate(
            total_debit=Sum(Case(When(transaction_type='Debit', then='amount'),default=0,output_field=DecimalField())),
            total_credit=Sum(Case(When(transaction_type='Credit', then='amount'),default=0,output_field=DecimalField())),
            total_refund=Sum(Case(When(transaction_type='Refund', then='amount'),default=0,output_field=DecimalField()))
            )
        debit_amount = result['total_debit'] or 0
        credit_amount = result['total_credit'] or 0
        refund_amount = result['total_refund'] or 0
        net_balance = credit_amount - debit_amount + refund_amount
        return net_balance or 0
     

class DeliverySettings(models.Model):
    class Meta:
        db_table = 'business_deliverysettings'

    id = models.AutoField(primary_key=True)
    business_code = models.OneToOneField(BusinessDetail, to_field='code', on_delete=models.CASCADE)
    store_address = models.CharField(max_length=255, blank=True, null=True)
    store_area = models.CharField(max_length=255, blank=True, null=True)
    store_city = models.CharField(max_length=100, blank=True, null=True)
    store_pin = models.CharField(max_length=10, blank=True, null=True)
    delivery_free = models.BooleanField(default=True)
    ship_free = models.BooleanField(default=True)
    min_amount_free_delivery = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Delivery Settings - {self.business_code_id}"


class DeliveryZone(models.Model):
    class Meta:
        db_table = 'business_deliveryzone'

    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]

    id = models.AutoField(primary_key=True)
    business_code = models.ForeignKey(BusinessDetail, to_field='code', on_delete=models.CASCADE)
    zone_name = models.CharField(max_length=100)
    pincode_to = models.CharField(max_length=10)
    distance_range_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    base_charge = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.zone_name} ({self.pincode_to})"


class WalletTransaction(models.Model):
    class Meta:
        db_table = 'business_wallettransaction'

    TRANSACTION_TYPE_CHOICES = [
        ('Debit', 'Debit'),
        ('Credit', 'Credit'),
        ('Refund', 'Refund')
    ]

    id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=100, db_index=True)
    avs_customer_name = models.CharField(max_length=255)
    avs_customer_id = models.CharField(max_length=50)
    avs_customer_mobile = models.CharField(max_length=20)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_order = models.ForeignKey(Order, to_field='order_id', on_delete=models.SET_NULL, blank=True, null=True)
    transaction_date = models.DateTimeField()
    transaction_for = models.CharField(max_length=255, blank=True, null=True)
    transaction_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.avs_customer_name} ({self.transaction_type})"


class Refund(models.Model):
    REFUND_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Refunded', 'Refunded'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]
    
    id = models.AutoField(primary_key=True)
    reference_order = models.ForeignKey(Order, to_field='order_id', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=50)
    customer_status = models.CharField(max_length=50)
    seller_status = models.CharField(max_length=50, default='Pending')
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='Pending')
    refunded_by = models.CharField(max_length=100, blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    cancellation_reason = models.TextField()
    refund_reason = models.TextField(blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'refund'
    
    def __str__(self):
        return f"Refund for {self.reference_order.order_id} - ₹{self.amount}"
