from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class StaffUser(models.Model):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)
    disabled_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'staff_user'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    @property
    def user_role(self):
        try:
            staff = Staff.objects.get(username=self.username)
            return staff.staff_role
        except Staff.DoesNotExist:
            return 'Staff'

class StaffUserProfile(models.Model):
    username = models.OneToOneField(StaffUser, to_field='username', on_delete=models.CASCADE, related_name='profile')
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    address3 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    phone1 = models.CharField(max_length=20, blank=True, null=True)
    phone2 = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'staff_user_profile'
    
    def __str__(self):
        return f"{self.full_name} - Profile"
    
    @property
    def full_name(self):
        names = [self.username.first_name]
        if self.username.middle_name:
            names.append(self.username.middle_name)
        names.append(self.username.last_name)
        return ' '.join(names)
    
    @property
    def email(self):
        return self.username.email

@receiver(post_save, sender=StaffUser)
def create_staff_user_profile(sender, instance, created, **kwargs):
    if created:
        StaffUserProfile.objects.create(
            username=instance,
            phone1=instance.phone
        )

from users.models import Customer

class BusinessDetail(models.Model):
    BUSINESS_TYPE_CHOICES = [
        ('Seller', 'Seller'),
        ('Shop', 'Shop'),
        ('Retailer', 'Retailer'),
        ('Service', 'Service'),
        ('None', 'None'),
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

class Staff(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    STAFF_ROLE_CHOICES = [
        ('Seller-Admin', 'Seller-Admin'),
        ('Shop-Admin', 'Shop-Admin'),
        ('Seller-Staff', 'Seller-Staff'),
        ('Shop-Staff', 'Shop-Staff'),
        ('Management-Admin', 'Management-Admin'),
        ('Management-Staff', 'Management-Staff'),
    ]
    
    username = models.ForeignKey(StaffUser, to_field='username', on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=50, unique=True, primary_key=True)
    business_code = models.ForeignKey(BusinessDetail, to_field='code', on_delete=models.CASCADE)
    staff_role = models.CharField(max_length=100, choices=STAFF_ROLE_CHOICES)
    phone = models.CharField(max_length=20)
    created_by = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
    @property
    def full_name(self):
        names = [self.username.first_name]
        if self.username.middle_name:
            names.append(self.username.middle_name)
        names.append(self.username.last_name)
        return ' '.join(names)
    
    @property
    def email(self):
        return self.username.email
    
    def __str__(self):
        return f"{self.full_name} - {self.staff_role}"

class StaffPrivileges(models.Model):
    staff = models.OneToOneField(Staff, to_field='staff_id', on_delete=models.CASCADE, related_name='privileges')
    manage_orders = models.BooleanField(default=False)
    manage_products = models.BooleanField(default=False)
    manage_reports = models.BooleanField(default=False)
    manage_payments = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'staff_privileges'
    
    def __str__(self):
        return f"Privileges for {self.staff.full_name}"

class ProductCategory(models.Model):
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
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    description = models.TextField()
    product_category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=50)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
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
    
    def __str__(self):
        return self.product_name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
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
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Net Banking', 'Net Banking'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
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
    sold_by = models.CharField(max_length=100)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Placed')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    placed_type = models.CharField(max_length=20, choices=PLACED_TYPE_CHOICES)
    old_order_id = models.CharField(max_length=50, blank=True, null=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='New')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    placed_by = models.CharField(max_length=100)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    confirmed_by = models.CharField(max_length=100, blank=True, null=True)
    processing_at = models.DateTimeField(blank=True, null=True)
    processing_by = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    shipped_by = models.CharField(max_length=100, blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    delivered_by = models.CharField(max_length=100, blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancelled_by = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
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
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Successful', 'Successful'),
        ('Failed', 'Failed'),
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
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    processing_at = models.DateTimeField(blank=True, null=True)
    processing_by = models.CharField(max_length=100, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} - ₹{self.amount}"

class UnitOfMeasurement(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Wallet(models.Model):
    WALLET_TYPE_CHOICES = [
        ('AVS', 'AVS'),
        ('Other', 'Other'),        
    ]
    
    wallet_id = models.CharField(max_length=50, primary_key=True)
    user_id = models.ForeignKey(Customer, to_field='username', on_delete=models.CASCADE, blank=True, null=True)
    wallet_type = models.CharField(max_length=50, choices=WALLET_TYPE_CHOICES)
    wallet_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    customer_name = models.CharField(max_length=255)
    customer_id = models.CharField(max_length=50)
    customer_mobile = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.customer_name} - Wallet ({self.wallet_id})"
