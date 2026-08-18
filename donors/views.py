from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings

from .models import Donor, AllowedUser
from .forms import DonorForm
from .services import get_notification_service

# --- NOTIFICATION HELPER ---

def send_donor_notification(donor):
    """
    Sends welcome/invitation notifications via configured channels (e.g. 'email,whatsapp', 'email', 'whatsapp', or 'all').
    """
    channels_setting = getattr(settings, 'NOTIFICATION_CHANNEL', 'email,whatsapp').lower()
    
    if channels_setting == 'all':
        channels = ['email', 'whatsapp']
    else:
        channels = [c.strip() for c in channels_setting.split(',') if c.strip()]
        
    results = []
    messages_list = []
    
    for channel in channels:
        if channel == 'email':
            if not donor.email:
                messages_list.append("Email skipped (no email address)")
                continue
            service = get_notification_service('email')
            success = service.send_welcome_notification(donor)
            if success:
                results.append(True)
                messages_list.append("Email sent successfully")
            else:
                results.append(False)
                messages_list.append("Email failed")
                
        elif channel == 'whatsapp':
            if not donor.mobile_number:
                messages_list.append("WhatsApp skipped (no mobile number)")
                continue
            service = get_notification_service('whatsapp')
            success = service.send_welcome_notification(donor)
            if success:
                results.append(True)
                messages_list.append("WhatsApp invitation sent successfully")
            else:
                results.append(False)
                messages_list.append("WhatsApp invitation failed")

        elif channel == 'sms':
            if not donor.mobile_number:
                messages_list.append("SMS skipped (no mobile number)")
                continue
            service = get_notification_service('sms')
            success = service.send_welcome_notification(donor)
            if success:
                results.append(True)
                messages_list.append("SMS sent successfully")
            else:
                results.append(False)
                messages_list.append("SMS failed")
                
    overall_success = any(results) if results else False
    summary_msg = " | ".join(messages_list) if messages_list else "No active notification channels."
    return overall_success, summary_msg


# --- USER AUTHENTICATION VIEWS (USERNAME ONLY, CASE-INSENSITIVE) ---

@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        raw_username = request.POST.get('username', '').strip()
        if not raw_username:
            messages.error(request, "Please enter your username.")
        else:
            username_lower = raw_username.lower()
            allowed = AllowedUser.objects.filter(username=username_lower, is_active=True).first()
            if allowed:
                # Retrieve or create Django User object for session state
                user, created = User.objects.get_or_create(username=allowed.username)
                if created:
                    user.set_unusable_password()
                    user.save()
                
                # Authenticate and login using Django session framework
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.session.set_expiry(18000)  # Session automatically expires after 5 hours (18000s)
                messages.success(request, f"Welcome, {allowed.username.capitalize()}! Successfully logged in.")
                return redirect('dashboard')
            else:
                messages.error(
                    request,
                    f"Access Denied: Username '{raw_username}' is not authorized to access this website. "
                    "Please contact an administrator."
                )

    return render(request, 'donors/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


# --- SUPERUSER ADMIN PANEL VIEWS ---

@ensure_csrf_cookie
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_panel')


    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            request.session.set_expiry(18000)  # Session automatically expires after 5 hours (18000s)
            messages.success(request, f"Superuser session initiated for '{user.username}'.")
            return redirect('admin_panel')

        else:
            messages.error(request, "Invalid superuser credentials or insufficient administrator privileges.")

    return render(request, 'donors/admin_login.html')


def admin_panel_view(request):
    if not (request.user.is_authenticated and request.user.is_superuser):
        messages.error(request, "Access restricted to superuser administrators.")
        return redirect('admin_login')

    users = AllowedUser.objects.all().order_by('-created_at')
    return render(request, 'donors/admin_panel.html', {'users': users})


@require_POST
def admin_add_user_view(request):
    if not (request.user.is_authenticated and request.user.is_superuser):
        messages.error(request, "Access restricted to superuser administrators.")
        return redirect('admin_login')

    new_username = request.POST.get('username', '').strip().lower()
    if not new_username:
        messages.error(request, "Username cannot be empty.")
    elif len(new_username) < 2:
        messages.error(request, "Username must be at least 2 characters long.")
    else:
        if AllowedUser.objects.filter(username=new_username).exists():
            messages.warning(request, f"Username '{new_username}' is already in the allowed access list.")
        else:
            AllowedUser.objects.create(username=new_username)
            messages.success(request, f"User '{new_username}' successfully added and authorized for website access.")

    return redirect('admin_panel')


@require_POST
def admin_delete_user_view(request, pk):
    if not (request.user.is_authenticated and request.user.is_superuser):
        messages.error(request, "Access restricted to superuser administrators.")
        return redirect('admin_login')

    allowed_user = get_object_or_404(AllowedUser, pk=pk)
    username = allowed_user.username
    allowed_user.delete()
    messages.success(request, f"Access permission for username '{username}' was successfully removed.")

    return redirect('admin_panel')


def admin_logout_view(request):
    logout(request)
    messages.info(request, "Superuser logged out successfully.")
    return redirect('admin_login')



# --- DASHBOARD VIEW ---

@login_required
def dashboard_view(request):
    # Retrieve donor metrics
    total_donors = Donor.objects.count()
    paid_donors = Donor.objects.filter(payment_status='PAID').count()
    due_donors = Donor.objects.filter(payment_status='DUE').count()
    
    # Calculate amounts
    total_collected_dict = Donor.objects.filter(payment_status='PAID').aggregate(total=Sum('amount'))
    total_collected = total_collected_dict['total'] or 0.00
    
    total_due_dict = Donor.objects.filter(payment_status='DUE').aggregate(total=Sum('amount'))
    total_due = total_due_dict['total'] or 0.00
    
    # Fetch recent donor activity (last 10 entries)
    recent_donors = Donor.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_donors': total_donors,
        'paid_donors': paid_donors,
        'due_donors': due_donors,
        'total_collected': total_collected,
        'total_due': total_due,
        'recent_donors': recent_donors
    }
    return render(request, 'donors/dashboard.html', context)


# --- DONOR ADD & EDIT VIEWS ---

@login_required
def donor_add_view(request):
    if request.method == 'POST':
        form = DonorForm(request.POST)
        if form.is_valid():
            donor = form.save(commit=False)
            
            # Auto set date if paid
            if donor.payment_status == 'PAID':
                if not donor.payment_date:
                    donor.payment_date = timezone.now()
            else:
                donor.payment_date = None
                
            donor.save()
            
            # Trigger welcome notification if status is PAID
            email_status_msg = ""
            if donor.payment_status == 'PAID':
                success, msg = send_donor_notification(donor)
                email_status_msg = " " + msg
                
            messages.success(request, f"Donor '{donor.name}' registered successfully.{email_status_msg}")
            return redirect('dashboard')
        else:
            messages.error(request, "Error creating donor record. Please check the inputs below.")
    else:
        form = DonorForm(initial={'payment_status': 'DUE'})
        
    return render(request, 'donors/add_donor.html', {'form': form, 'title': 'Add Donor / Collect Chanda'})

@login_required
def donor_edit_view(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    old_status = donor.payment_status
    
    if request.method == 'POST':
        form = DonorForm(request.POST, instance=donor)
        if form.is_valid():
            edited_donor = form.save(commit=False)
            
            # Check if status transitions from DUE to PAID
            trigger_notification = False
            if old_status == 'DUE' and edited_donor.payment_status == 'PAID':
                trigger_notification = True
                if not edited_donor.payment_date:
                    edited_donor.payment_date = timezone.now()
            elif edited_donor.payment_status == 'DUE':
                edited_donor.payment_date = None
                
            edited_donor.save()
            
            email_status_msg = ""
            if trigger_notification:
                success, msg = send_donor_notification(edited_donor)
                email_status_msg = " " + msg
            
            messages.success(request, f"Donor '{edited_donor.name}' updated successfully.{email_status_msg}")
            return redirect('donor_detail', pk=edited_donor.pk)
        else:
            messages.error(request, "Error updating donor record. Please check the inputs below.")
    else:
        form = DonorForm(instance=donor)
        
    return render(request, 'donors/donor_edit.html', {
        'form': form, 
        'donor': donor,
        'title': f"Edit Donor: {donor.name}"
    })


# --- DONOR LIST VIEWS ---

@login_required
def donor_list_paid_view(request):
    query = request.GET.get('q', '')
    donors_list = Donor.objects.filter(payment_status='PAID').order_by('-payment_date')
    
    if query:
        donors_list = donors_list.filter(
            Q(name__icontains=query) |
            Q(mobile_number__icontains=query) |
            Q(email__icontains=query) |
            Q(address__icontains=query)
        )
        
    paginator = Paginator(donors_list, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'donors/paid.html', {
        'page_obj': page_obj, 
        'query': query,
        'total_count': donors_list.count()
    })

@login_required
def donor_list_due_view(request):
    query = request.GET.get('q', '')
    donors_list = Donor.objects.filter(payment_status='DUE').order_by('-created_at')
    
    if query:
        donors_list = donors_list.filter(
            Q(name__icontains=query) |
            Q(mobile_number__icontains=query) |
            Q(email__icontains=query) |
            Q(address__icontains=query)
        )
        
    paginator = Paginator(donors_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'donors/due.html', {
        'page_obj': page_obj, 
        'query': query,
        'total_count': donors_list.count()
    })

@login_required
def donor_list_all_view(request):
    query = request.GET.get('q', '')
    donors_list = Donor.objects.all().order_by('-created_at')
    
    if query:
        donors_list = donors_list.filter(
            Q(name__icontains=query) |
            Q(mobile_number__icontains=query) |
            Q(email__icontains=query) |
            Q(address__icontains=query)
        )
        
    paginator = Paginator(donors_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'donors/all.html', {
        'page_obj': page_obj, 
        'query': query,
        'total_count': donors_list.count()
    })


# --- DONOR DETAIL, DELETE & ACTION VIEWS ---

@login_required
def donor_detail_view(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    return render(request, 'donors/donor_detail.html', {'donor': donor})

@login_required
def donor_mark_paid_view(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    
    if donor.payment_status == 'PAID':
        messages.info(request, f"Donor '{donor.name}' is already marked as PAID.")
        return redirect('donor_detail', pk=donor.pk)
        
    if request.method == 'POST':
        donor.payment_status = 'PAID'
        donor.payment_date = timezone.now()
        donor.save(update_fields=['payment_status', 'payment_date'])
        
        success, msg = send_donor_notification(donor)
        email_status_msg = " " + msg
            
        messages.success(request, f"Donor '{donor.name}' marked as PAID.{email_status_msg}")
        
    return redirect('donor_detail', pk=donor.pk)

@login_required
def donor_delete_view(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    
    if request.method == 'POST':
        from django.contrib.auth.models import User
        admin_password = request.POST.get('admin_password', '').strip()
        
        # Verify password against request.user or active superuser accounts
        is_authenticated = False
        if request.user.is_authenticated and request.user.check_password(admin_password):
            is_authenticated = True
        else:
            # Check against superusers (e.g. jagadeesh)
            superusers = User.objects.filter(is_superuser=True)
            for su in superusers:
                if su.check_password(admin_password):
                    is_authenticated = True
                    break
                    
        if is_authenticated:
            name = donor.name
            donor.delete()
            messages.success(request, f"Donor '{name}' was deleted successfully after admin verification.")
            return redirect('dashboard')
        else:
            messages.error(request, "Security Authentication Failed: Invalid admin password. Deletion denied.")
            
    return render(request, 'donors/donor_confirm_delete.html', {'donor': donor})


# --- RETRY NOTIFICATION VIEW ---

@login_required
def donor_retry_notification_view(request, pk):
    donor = get_object_or_404(Donor, pk=pk)
    
    if donor.payment_status != 'PAID':
        messages.error(request, f"Welcome notifications can only be sent to PAID donors. Current status: {donor.payment_status}")
        return redirect('donor_detail', pk=donor.pk)
        
    success, msg = send_donor_notification(donor)
    if success:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
        
    return redirect('donor_detail', pk=donor.pk)


# --- GLOBAL SEARCH VIEW ---

@login_required
def donor_search_view(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'ALL').strip()
    min_amount = request.GET.get('min_amount', '').strip()
    max_amount = request.GET.get('max_amount', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    
    donors = Donor.objects.all()
    
    # 1. Text Search across fields
    if query:
        donors = donors.filter(
            Q(name__icontains=query) |
            Q(mobile_number__icontains=query) |
            Q(email__icontains=query) |
            Q(address__icontains=query)
        )
        
    # 2. Status Filter
    if status in ['PAID', 'DUE']:
        donors = donors.filter(payment_status=status)
        
    # 3. Amount Filters
    if min_amount:
        try:
            donors = donors.filter(amount__gte=float(min_amount))
        except ValueError:
            pass
    if max_amount:
        try:
            donors = donors.filter(amount__lte=float(max_amount))
        except ValueError:
            pass
            
    # 4. Date Filters (based on creation date)
    if start_date:
        try:
            donors = donors.filter(created_at__date__gte=start_date)
        except Exception:
            pass
    if end_date:
        try:
            donors = donors.filter(created_at__date__lte=end_date)
        except Exception:
            pass
            
    context = {
        'donors': donors,
        'query': query,
        'status': status,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'start_date': start_date,
        'end_date': end_date,
        'total_results': donors.count()
    }
    return render(request, 'donors/search_results.html', context)
