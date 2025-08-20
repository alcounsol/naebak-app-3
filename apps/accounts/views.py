"""
Views for accounts app
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User
from .models import Citizen
from apps.core.models import Governorate


def user_login(request):
    """
    User login view
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'تم تسجيل الدخول بنجاح.')
            # Use absolute URL redirect to avoid broken links
            return redirect('/')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
    
    return render(request, 'accounts/login.html')


def user_logout(request):
    """
    User logout view
    """
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح.')
    return redirect('core:home')


def citizen_register(request):
    """
    Citizen registration view
    """
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        governorate = request.POST.get('governorate', '').strip()
        area_type = request.POST.get('area_type', '').strip()
        area_name = request.POST.get('area_name', '').strip()
        address = request.POST.get('address', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Validate form data
        if not all([first_name, last_name, email, phone, governorate, area_type, area_name, address, password1, password2]):
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
            return render(request, 'accounts/register.html')
        
        if password1 != password2:
            messages.error(request, 'كلمات المرور غير متطابقة.')
            return render(request, 'accounts/register.html')
        
        if len(password1) < 6:
            messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل.')
            return render(request, 'accounts/register.html')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'يوجد حساب مسجل بهذا البريد الإلكتروني بالفعل.')
            return render(request, 'accounts/register.html')
        
        # Create username from email
        username = email.split('@')[0]
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Get or create governorate
            governorate_obj, created = Governorate.objects.get_or_create(
                name=governorate
            )
            
            # Create citizen profile
            citizen = Citizen.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone,
                governorate=governorate_obj,
                area_type=area_type,
                area_name=area_name,
                address=address
            )
            
            # Log the user in automatically
            login(request, user)
            
            messages.success(request, f'مرحباً {first_name}! تم إنشاء حسابك بنجاح.')
            # Use absolute URL redirect to avoid broken links
            return redirect('/')
            
        except Exception as e:
            print(f"Registration error: {e}")  # For debugging
            messages.error(request, 'حدث خطأ أثناء إنشاء الحساب. يرجى المحاولة مرة أخرى.')
            return render(request, 'accounts/register.html')
    
    return render(request, 'accounts/register.html')


@login_required
def citizen_profile(request):
    """
    Citizen profile view
    """
    return render(request, 'accounts/profile.html')


@login_required
def edit_citizen_profile(request):
    """
    Edit citizen profile view
    """
    if request.method == 'POST':
        # Handle profile update logic here
        messages.success(request, 'تم تحديث الملف الشخصي بنجاح.')
        return redirect('accounts:citizen_profile')
    
    return render(request, 'accounts/edit_profile.html')



def quick_login(request):
    """
    Quick login view from landing page
    """
    if request.method == 'POST':
        governorate_name = request.POST.get("governorate", "").strip()
        citizen_name = request.POST.get("citizen_name", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()

        # Validate input data
        if not governorate_name or not citizen_name or not phone_number:
            messages.error(request, 'يرجى ملء جميع حقول الدخول السريع.')
            return redirect('/')
        
        # Try to find a citizen with matching data
        try:
            # Look for a citizen with matching phone number and name
            citizen = Citizen.objects.filter(
                phone_number=phone_number,
                first_name__icontains=citizen_name.split()[0] if citizen_name.split() else citizen_name
            ).first()
            
            if citizen:
                # Log the user in
                login(request, citizen.user)
                messages.success(request, f'مرحباً {citizen.first_name}! تم تسجيل الدخول السريع بنجاح.')
                return redirect('/')
            else:
                # If no matching citizen found, suggest registration
                messages.warning(request, 'لم يتم العثور على حساب مطابق. يرجى التحقق من البيانات أو إنشاء حساب جديد.')
                return redirect('/')
                
        except Exception as e:
            print(f"Quick login error: {e}")  # For debugging
            messages.error(request, 'حدث خطأ أثناء محاولة تسجيل الدخول. يرجى المحاولة مرة أخرى.')
            return redirect('/')
    
    return redirect('/')


