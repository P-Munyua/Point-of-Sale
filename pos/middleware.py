# pos/middleware.py

from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class PermissionMiddleware:
    """Middleware to check user permissions"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Define URL patterns and required permissions
        self.permission_map = {
            # Dashboard
            '/dashboard/': 'can_access_dashboard',
            '/pos/': 'can_access_pos',
            
            # Sales
            '/sales/': 'can_view_all_sales',
            '/sales/create/': 'can_process_sales',
            '/sales/edit/': 'can_edit_sales',
            '/sales/delete/': 'can_delete_sales',
            
            # Products
            '/products/': 'can_view_products',
            '/products/add/': 'can_add_products',
            '/products/edit/': 'can_edit_products',
            '/products/delete/': 'can_delete_products',
            '/products/import/': 'can_import_products',
            
            # Inventory
            '/inventory/': 'can_view_inventory',
            '/inventory/manage/': 'can_manage_stock',
            '/inventory/reports/': 'can_view_reports',
            
            # Purchases
            '/purchases/': 'can_view_purchases',
            '/purchases/add/': 'can_add_purchases',
            '/purchases/edit/': 'can_edit_purchases',
            '/purchases/delete/': 'can_delete_purchases',
            
            # Reports
            '/reports/sales/': 'can_view_sales_reports',
            '/reports/inventory/': 'can_view_inventory_reports',
            '/reports/profit/': 'can_view_profit_reports',
            '/reports/customers/': 'can_view_customer_reports',
            '/reports/export/': 'can_export_reports',
            
            # Admin
            '/admin/users/': 'can_manage_users',
            '/admin/roles/': 'can_manage_roles',
            '/admin/settings/': 'can_manage_settings',
        }
    
    def __call__(self, request):
        # Skip permission check for login, logout, and static files
        if (request.path.startswith('/login/') or 
            request.path.startswith('/logout/') or
            request.path.startswith('/static/') or
            request.path.startswith('/media/')):
            return self.get_response(request)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return redirect('custom_login')
        
        # Admin users (superusers) bypass permission checks
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Check if user has profile and role
        if not hasattr(request.user, 'profile') or not request.user.profile.role:
            messages.error(request, 'Your account is not properly configured. Please contact administrator.')
            return redirect('custom_login')
        
        # Check permissions for the requested URL
        for url_pattern, required_permission in self.permission_map.items():
            if url_pattern in request.path:
                if not request.user.profile.has_permission(required_permission):
                    messages.error(request, 'You do not have permission to access this page.')
                    return redirect('dashboard')
                break
        
        return self.get_response(request)