from .models import Donor

def donor_counts(request):
    """
    Context processor to inject dynamic counts of PAID and DUE donors 
    into all templates for navbar display.
    """
    # Safeguard against db errors before migrations are run
    try:
        paid_count = Donor.objects.filter(payment_status='PAID').count()
        due_count = Donor.objects.filter(payment_status='DUE').count()
    except Exception:
        paid_count = 0
        due_count = 0
        
    return {
        'nav_paid_count': paid_count,
        'nav_due_count': due_count,
    }

def google_maps_key(request):
    """
    Context processor to inject the Google Maps API key into all templates 
    for Autocomplete integration.
    """
    from django.conf import settings
    return {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    }
