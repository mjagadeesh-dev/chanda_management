from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from .models import AllowedUser

class LoginRequiredMiddleware:
    """
    Middleware that enforces authentication for every view request across the application.
    Exempts login routes and static assets.
    """
    EXEMPT_EXACT_URLS = [
        '/login/',
        '/admin-panel/login/',
        '/logout/',
        '/admin-panel/logout/',
    ]
    
    EXEMPT_PREFIXES = [
        '/static/',
        '/media/',
        '/admin/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Check exact exemptions
        if path in self.EXEMPT_EXACT_URLS:
            return self.get_response(request)

        # Check prefix exemptions
        for prefix in self.EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # Unauthenticated user access control
        if not request.user.is_authenticated:
            if path.startswith('/admin-panel/'):
                return redirect('admin_login')
            return redirect('login')

        # Authenticated regular user check against AllowedUser list
        if not request.user.is_superuser:
            username_lower = request.user.username.strip().lower()
            allowed = AllowedUser.objects.filter(username=username_lower, is_active=True).exists()
            if not allowed:
                logout(request)
                messages.error(request, "Your access permission has been revoked or username is invalid.")
                return redirect('login')

        return self.get_response(request)
