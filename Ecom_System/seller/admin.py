from django.contrib import admin
from seller.models import  Staff, StaffUser, StaffUserProfile, StaffPrivileges

admin.site.register(Staff)
admin.site.register(StaffUser)
admin.site.register(StaffUserProfile)
admin.site.register(StaffPrivileges)
