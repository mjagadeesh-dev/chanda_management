from django.urls import path
from . import views

urlpatterns = [
    # General User Auth routes (Username only, passwordless)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Superuser Admin Panel routes
    path('admin-panel/login/', views.admin_login_view, name='admin_login'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('admin-panel/users/add/', views.admin_add_user_view, name='admin_add_user'),
    path('admin-panel/users/<int:pk>/delete/', views.admin_delete_user_view, name='admin_delete_user'),
    path('admin-panel/logout/', views.admin_logout_view, name='admin_logout'),

    # Core dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Donor routes
    path('donors/add/', views.donor_add_view, name='donor_add'),
    path('donors/paid/', views.donor_list_paid_view, name='donor_list_paid'),
    path('donors/due/', views.donor_list_due_view, name='donor_list_due'),
    path('donors/all/', views.donor_list_all_view, name='donor_list_all'),
    path('donors/<int:pk>/', views.donor_detail_view, name='donor_detail'),
    path('donors/<int:pk>/edit/', views.donor_edit_view, name='donor_edit'),
    path('donors/<int:pk>/mark-paid/', views.donor_mark_paid_view, name='donor_mark_paid'),
    path('donors/<int:pk>/delete/', views.donor_delete_view, name='donor_delete'),
    path('donors/<int:pk>/retry-notification/', views.donor_retry_notification_view, name='donor_retry_notification'),
    
    # Global search route
    path('donors/search/', views.donor_search_view, name='donor_search'),
]

