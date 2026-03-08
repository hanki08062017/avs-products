from business.models import Staff, StaffUser

def staff_info(request):
    if request.session.get('is_logged_in') and request.session.get('user_type') == 'staff':
        username = request.session.get('user_id')
        business_code = request.session.get('business_code')
        try:
            user = StaffUser.objects.get(username=username)
            staff = Staff.objects.get(username=user, business_code=business_code)
            is_admin = staff.staff_role in ['Seller-Admin', 'Shop-Admin']
            return {
                'staff_info': {
                    'name': staff.full_name,
                    'staff_id': staff.staff_id,
                    'role': staff.staff_role,
                    'is_admin': is_admin
                }
            }
        except (StaffUser.DoesNotExist, Staff.DoesNotExist):
            pass
    return {}
