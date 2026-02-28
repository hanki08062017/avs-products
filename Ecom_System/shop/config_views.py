from django.shortcuts import render, redirect
from django.contrib import messages
from business.models import ProductCategory, UnitOfMeasurement, GSTDetail, Staff, StaffUser

def config_view(request):
    if not request.session.get('is_logged_in'):
        return redirect('login')
    
    business_code = request.session.get('business_code')
    username = request.session.get('user_id')
    
    staff_user = StaffUser.objects.get(username=username)
    staff = Staff.objects.get(username=staff_user, business_code=business_code)
    
    categories = ProductCategory.objects.all()
    units = UnitOfMeasurement.objects.all()
    gst_details = GSTDetail.objects.filter(business_code=business_code)
    
    return render(request, 'shop/config.html', {
        'categories': categories,
        'units': units,
        'gst_details': gst_details,
        'business_code': business_code,
        'staff_info': {'name': staff.full_name, 'staff_id': staff.staff_id}
    })

def add_category(request):
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
    if request.method == 'POST':
        UnitOfMeasurement.objects.create(
            name=request.POST.get('name'),
            abbreviation=request.POST.get('abbreviation'),
            created_by=request.session.get('user_id')
        )
        messages.success(request, 'Unit added successfully!')
    return redirect('config')

def edit_unit(request, id):
    if request.method == 'POST':
        unit = UnitOfMeasurement.objects.get(id=id)
        unit.name = request.POST.get('name')
        unit.abbreviation = request.POST.get('abbreviation')
        unit.modified_by = request.session.get('user_id')
        unit.save()
        messages.success(request, 'Unit updated successfully!')
    return redirect('config')

def add_gst(request):
    if request.method == 'POST':
        business_code = request.session.get('business_code')
        username = request.session.get('user_id')
        
        staff_user = StaffUser.objects.get(username=username)
        staff = Staff.objects.get(username=staff_user, business_code=business_code)
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
    if request.method == 'POST':
        business_code = request.session.get('business_code')
        username = request.session.get('user_id')
        
        staff_user = StaffUser.objects.get(username=username)
        staff = Staff.objects.get(username=staff_user, business_code=business_code)
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
