from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard/')), # Redirect base URL to dashboard
    path('', include('donors.urls')), # Mount donors routes at root level
]
