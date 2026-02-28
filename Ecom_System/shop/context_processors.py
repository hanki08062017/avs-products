from business.models import Staff, StaffUser

def staff_info(request):
    if request.session.get('is_logged_in') and request.session.get('user_type') == 'staff':
        username = request.session.get('user_id')
        business_code = request.session.get('business_code')
        try:
            user = StaffUser.objects.get(username=username)
            staff = Staff.objects.get(username=user, business_code=business_code)
            return {
                'staff_info': {
                    'name': staff.full_name,
                    'staff_id': staff.staff_id,
                    'role': staff.staff_role
                }
            }
        except (StaffUser.DoesNotExist, Staff.DoesNotExist):
            pass
    return {}
