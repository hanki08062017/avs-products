from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Customer(models.Model):
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
        db_table = 'customer'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

class CustomerProfile(models.Model):
    username = models.OneToOneField(Customer, to_field='username', on_delete=models.CASCADE, related_name='profile')
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
        db_table = 'customer_profile'
    
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

@receiver(post_save, sender=Customer)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        CustomerProfile.objects.create(
            username=instance,
            phone1=instance.phone
        )

class SavedAddress(models.Model):
    ADDRESS_CHOICES = [
        ('Billing', 'Billing'),
        ('Shipping', 'Shipping'),
        ('Both', 'Both')
    ]
    customer = models.ForeignKey(Customer, to_field='username', on_delete=models.CASCADE, related_name='saved_addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_CHOICES)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_address'
    
    def __str__(self):
        return f"{self.customer.username} - {self.address_type}"

class SavedPaymentMethod(models.Model):
    customer = models.ForeignKey(Customer, to_field='username', on_delete=models.CASCADE, related_name='saved_payments')
    payment_type = models.CharField(max_length=20, choices=[('Card', 'Card'), ('UPI', 'UPI')])
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_name = models.CharField(max_length=255, blank=True, null=True)
    upi_id = models.CharField(max_length=255, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_payment_method'
    
    def __str__(self):
        return f"{self.customer.username} - {self.payment_type}"
