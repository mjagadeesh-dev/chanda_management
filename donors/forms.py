import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Donor

class DonorForm(forms.ModelForm):
    class Meta:
        model = Donor
        fields = [
            'name', 
            'mobile_number', 
            'email', 
            'amount', 
            'address', 
            'latitude', 
            'longitude', 
            'google_place_id', 
            'payment_status', 
            'payment_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Donor Name', 'required': 'required'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 10-digit Mobile Number', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email (Optional)'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Chanda Amount (₹)', 'min': '1', 'required': 'required'}),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Click the Get GPS Address button to retrieve location...', 
                'id': 'search-address-input',
                'readonly': 'readonly',
                'required': 'required'
            }),
            'latitude': forms.HiddenInput(attrs={'id': 'id_latitude'}),
            'longitude': forms.HiddenInput(attrs={'id': 'id_longitude'}),
            'google_place_id': forms.HiddenInput(attrs={'id': 'id_google_place_id'}),
            'payment_status': forms.Select(attrs={'class': 'form-select', 'id': 'id_payment_status'}),
            # We use an input field for payment date, editable but automatically pre-populated via JS/views
            'payment_date': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local', 'id': 'id_payment_date'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Payment date is not strictly required upon initial creation if status is DUE
        self.fields['payment_date'].required = False
        # Latitude, Longitude and Google Place ID are populated via JS so they are blank=True in forms
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['google_place_id'].required = False

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number', '').strip()
        # Regex matching standard Indian mobile number formats:
        # - Optional country prefix (+91 or 91 or 0)
        # - Starts with 6, 7, 8, or 9
        # - Followed by 9 digits
        pattern = r'^(?:\+91|91|0)?[6-9]\d{9}$'
        if not re.match(pattern, mobile):
            raise ValidationError("Enter a valid Indian mobile number (e.g. 9876543210).")
        
        # Standardize representation to simple 10 digit or +91 format if needed. Let's keep the last 10 digits or clean it:
        # Strip prefixes to store just the 10 digits or standard +91
        cleaned_mobile = mobile[-10:]
        return cleaned_mobile

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise ValidationError("Donation amount must be greater than zero.")
        return amount
