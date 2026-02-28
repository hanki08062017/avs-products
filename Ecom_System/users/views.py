from django.shortcuts import render, redirect
from django.contrib import messages
from business.models import StaffUser, StaffUserProfile

def staff_profile_edit(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    username = request.session.get('user_id')
    business_code = request.session.get('business_code')
    staff_user = StaffUser.objects.get(username=username)
    profile = staff_user.profile
    
    from business.models import Staff
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    
    if request.method == 'POST':
        staff_user.first_name = request.POST.get('first_name')
        staff_user.middle_name = request.POST.get('middle_name', '')
        staff_user.last_name = request.POST.get('last_name')
        staff_user.email = request.POST.get('email')
        staff_user.phone = request.POST.get('phone')
        staff_user.save()
        
        profile.address1 = request.POST.get('address1', '')
        profile.address2 = request.POST.get('address2', '')
        profile.address3 = request.POST.get('address3', '')
        profile.city = request.POST.get('city', '')
        profile.state = request.POST.get('state', '')
        profile.pin = request.POST.get('pin', '')
        profile.country = request.POST.get('country', '')
        profile.phone1 = request.POST.get('phone1', '')
        profile.phone2 = request.POST.get('phone2', '')
        
        if request.FILES.get('profile_pic'):
            profile.profile_pic = request.FILES['profile_pic']
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('staff_profile_edit')
    
    return render(request, 'users/staff_profile_edit.html', {
        'staff_user': staff_user,
        'profile': profile,
        'staff': staff
    })
