from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from management.models import ProductCategory, UnitOfMeasurement, GSTDetail, DeliveryZone, DeliveryWeightSlab, DeliverySettings
from .models import Staff, StaffUser

def config_view(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    is_admin = staff.staff_role in ['Seller-Admin', 'Shop-Admin']
    
    categories = ProductCategory.objects.all()
    units = UnitOfMeasurement.objects.all()
    gst_details = GSTDetail.objects.filter(business_code=business_code)
    
    delivery_zones = DeliveryZone.objects.filter(business_code=business_code)
    weight_slabs = DeliveryWeightSlab.objects.filter(business_code=business_code)
    delivery_settings, _ = DeliverySettings.objects.get_or_create(business_code_id=business_code)

    return render(request, 'seller/config.html', {
        'categories': categories,
        'units': units,
        'gst_details': gst_details,
        'delivery_zones': delivery_zones,
        'weight_slabs': weight_slabs,
        'delivery_settings': delivery_settings,
        'business_code': business_code,
        'is_admin': is_admin,
        'staff_info': {'name': staff.full_name, 'staff_id': staff.staff_id},
        'user': staff_user
    })

def add_category(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    # Check if user is admin
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'You do not have permission to add categories.')
        return redirect('config')
    
    if request.method == 'POST':
        ProductCategory.objects.create(
            category=request.POST.get('category'),
            sub_category=request.POST.get('sub_category'),
            hsn=request.POST.get('hsn'),
            sgst=request.POST.get('sgst'),
            cgst=request.POST.get('cgst'),
            created_by=request.session.get('user_id')
        )
        messages.success(request, 'Category added successfully!')
    return redirect('config')

def edit_category(request, id):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    # Check if user is admin
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'You do not have permission to edit categories.')
        return redirect('config')
    
    if request.method == 'POST':
        category = ProductCategory.objects.get(id=id)
        category.category = request.POST.get('category')
        category.sub_category = request.POST.get('sub_category')
        category.hsn = request.POST.get('hsn')
        category.sgst = request.POST.get('sgst')
        category.cgst = request.POST.get('cgst')
        category.modified_by = request.session.get('user_id')
        category.save()
        messages.success(request, 'Category updated successfully!')
    return redirect('config')

def add_unit(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    # Check if user is admin
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'You do not have permission to add units.')
        return redirect('config')
    
    if request.method == 'POST':
        UnitOfMeasurement.objects.create(
            name=request.POST.get('name'),
            abbreviation=request.POST.get('abbreviation'),
            created_by=request.session.get('user_id')
        )
        messages.success(request, 'Unit added successfully!')
    return redirect('config')

def edit_unit(request, id):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    # Check if user is admin
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'You do not have permission to edit units.')
        return redirect('config')
    
    if request.method == 'POST':
        unit = UnitOfMeasurement.objects.get(id=id)
        unit.name = request.POST.get('name')
        unit.abbreviation = request.POST.get('abbreviation')
        unit.modified_by = request.session.get('user_id')
        unit.save()
        messages.success(request, 'Unit updated successfully!')
    return redirect('config')

def add_gst(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    # Check if user is admin
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'You do not have permission to add GST details.')
        return redirect('config')
    
    if request.method == 'POST':
        created_by = staff.full_name
        
        GSTDetail.objects.create(
            gst_number=request.POST.get('gst_number'),
            pan=request.POST.get('pan'),
            reg_date=request.POST.get('reg_date'),
            valid_till=request.POST.get('valid_till'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            pin=request.POST.get('pin'),
            country=request.POST.get('country'),
            business_code_id=business_code,
            created_by=created_by
        )
        messages.success(request, 'GST details added successfully!')
    return redirect('config')

def edit_gst(request, id):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    # Check if user is admin
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'You do not have permission to edit GST details.')
        return redirect('config')
    
    if request.method == 'POST':
        modified_by = staff.full_name
        
        gst = GSTDetail.objects.get(serial_no=id)
        gst.gst_number = request.POST.get('gst_number')
        gst.pan = request.POST.get('pan')
        gst.reg_date = request.POST.get('reg_date')
        gst.valid_till = request.POST.get('valid_till')
        gst.address = request.POST.get('address')
        gst.city = request.POST.get('city')
        gst.pin = request.POST.get('pin')
        gst.country = request.POST.get('country')
        gst.status = request.POST.get('status')
        gst.modified_by = modified_by
        gst.save()
        messages.success(request, 'GST details updated successfully!')
    return redirect('config')


def add_delivery_charge(request):
    pass

def edit_delivery_charge(request, id):
    pass


def save_delivery_settings(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'No permission.')
        return redirect('config')
    if request.method == 'POST':
        settings, _ = DeliverySettings.objects.get_or_create(business_code_id=business_code)
        settings.store_address = request.POST.get('store_address')
        settings.store_area = request.POST.get('store_area')
        settings.store_city = request.POST.get('store_city')
        settings.store_pin = request.POST.get('store_pin')
        settings.min_amount_free_delivery = request.POST.get('min_amount_free_delivery') or 0
        settings.max_distance_km = request.POST.get('max_distance_km') or 0
        settings.modified_by = staff.full_name
        settings.save()
        messages.success(request, 'Delivery settings saved!')
    return redirect('config')


def add_delivery_zone(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'No permission.')
        return redirect('config')
    if request.method == 'POST':
        DeliveryZone.objects.create(
            business_code_id=business_code,
            zone_name=request.POST.get('zone_name'),
            pincode_to=request.POST.get('pincode_to'),
            distance_range_km=request.POST.get('distance_range_km') or None,
            base_charge=request.POST.get('base_charge'),
            created_by=staff.full_name,
        )
        messages.success(request, 'Delivery zone added successfully!')
    return redirect('config')


def edit_delivery_zone(request, id):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'No permission.')
        return redirect('config')
    if request.method == 'POST':
        zone = DeliveryZone.objects.get(id=id)
        zone.zone_name = request.POST.get('zone_name')
        zone.pincode_to = request.POST.get('pincode_to')
        zone.distance_range_km = request.POST.get('distance_range_km') or None
        zone.base_charge = request.POST.get('base_charge')
        zone.status = request.POST.get('status')
        zone.modified_by = staff.full_name
        zone.save()
        messages.success(request, 'Delivery zone updated successfully!')
    return redirect('config')


def add_weight_slab(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'No permission.')
        return redirect('config')
    if request.method == 'POST':
        DeliveryWeightSlab.objects.create(
            business_code_id=business_code,
            slab_name=request.POST.get('slab_name'),
            weight_from_kg=request.POST.get('weight_from_kg'),
            weight_to_kg=request.POST.get('weight_to_kg'),
            extra_charge=request.POST.get('extra_charge'),
            created_by=staff.full_name,
        )
        messages.success(request, 'Weight slab added successfully!')
    return redirect('config')


def edit_weight_slab(request, id):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    if staff.staff_role not in ['Seller-Admin', 'Shop-Admin']:
        messages.error(request, 'No permission.')
        return redirect('config')
    if request.method == 'POST':
        slab = DeliveryWeightSlab.objects.get(id=id)
        slab.slab_name = request.POST.get('slab_name')
        slab.weight_from_kg = request.POST.get('weight_from_kg')
        slab.weight_to_kg = request.POST.get('weight_to_kg')
        slab.extra_charge = request.POST.get('extra_charge')
        slab.status = request.POST.get('status')
        slab.modified_by = staff.full_name
        slab.save()
        messages.success(request, 'Weight slab updated successfully!')
    return redirect('config')


def check_delivery_charge(request):
    if not request.session.get('is_logged_in'):
        return JsonResponse({'success': False, 'error': 'Not logged in'})
    business_code = request.session.get('business_code')
    ship_pin = request.GET.get('ship_pin', '').strip()
    weight = request.GET.get('weight', '0')
    try:
        weight = float(weight)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid weight'})

    zone = DeliveryZone.objects.filter(
        business_code=business_code,
        status='Active',
        pincode_to=ship_pin
    ).first()

    if not zone:
        return JsonResponse({'success': False, 'error': 'No delivery zone found for this pincode'})

    weight_slab = DeliveryWeightSlab.objects.filter(
        business_code=business_code,
        status='Active',
        weight_from_kg__lte=weight,
        weight_to_kg__gte=weight
    ).first()

    weight_charge = float(weight_slab.extra_charge) if weight_slab else 0
    total_charge = float(zone.base_charge) + weight_charge

    return JsonResponse({
        'success': True,
        'zone_name': zone.zone_name,
        'distance_range': str(zone.distance_range_km) if zone.distance_range_km else '-',
        'base_charge': float(zone.base_charge),
        'weight_slab': weight_slab.slab_name if weight_slab else 'No slab matched',
        'weight_charge': weight_charge,
        'total_charge': total_charge,
        'estimated_days': '-',
    })
