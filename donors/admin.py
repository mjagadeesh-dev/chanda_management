from django.contrib import admin
from .models import Donor, AllowedUser


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile_number', 'amount', 'payment_status', 'payment_date', 'created_at')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('name', 'mobile_number', 'email', 'address')

@admin.register(AllowedUser)
class AllowedUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_active', 'created_at')
    search_fields = ('username',)

