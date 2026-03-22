import os
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from management.models import BusinessDetail

def _staff_pic_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    name = f"{instance.username.first_name}_{instance.username.last_name}{ext}"
    return f"seller/{instance.username.username}/{name}"

# Create your models here.
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
        app_label = 'seller'
    
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
    profile_pic = models.ImageField(upload_to=_staff_pic_path, blank=True, null=True)
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    address3 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    phone1 = models.CharField(max_length=20, blank=True, null=True)
    phone2 = models.CharField(max_length=20, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)
    aadhaar_attachment = models.FileField(upload_to='staff_kyc/', blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    pan_attachment = models.FileField(upload_to='staff_kyc/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'staff_user_profile'
        app_label = 'seller'
    
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


class Staff(models.Model):
    class Meta:
        db_table = 'business_staff'
        app_label = 'seller'

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    
    STAFF_ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Staff', 'Staff'),
    ]
    
    username = models.ForeignKey(StaffUser, to_field='username', on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=50, unique=True, primary_key=True)
    business_code = models.ForeignKey(BusinessDetail, to_field='code', on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=STAFF_ROLE_CHOICES)
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
    
    @property
    def staff_role(self):
        return f"{self.business_code.business_type}-{self.role}"


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
        app_label = 'seller'
    
    def __str__(self):
        return f"Privileges for {self.staff.full_name}"