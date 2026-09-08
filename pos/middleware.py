# pos/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse, resolve
from django.http import HttpResponseForbidden
import re
from threading import local

# Thread local storage for request object
_request_local = local()

class RequestMiddleware:
    """
    Middleware to capture request object for signals
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request in thread local for signals
        _request_local.request = request
        response = self.get_response(request)
        return response


class PermissionMiddleware:
    """Middleware to check user permissions"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define URL patterns with their required permissions
        self.permission_map = [
            # Dashboard & POS
            (r'^/dashboard/$', 'can_access_dashboard'),
            (r'^/pos/$', 'can_access_pos'),
            (r'^/pos/\d+/$', 'can_access_pos'),
            (r'^/process-sale/$', 'can_process_sales'),
            
            # Sales
            (r'^/sales-report/$', 'can_view_all_sales'),
            (r'^/sale/\d+/$', 'can_view_all_sales'),
            (r'^/edit-sale/\d+/$', 'can_edit_sales'),
            (r'^/delete-sale/\d+/$', 'can_delete_sales'),
            (r'^/load-sale/\d+/$', 'can_edit_sales'),
            (r'^/daily-sales-report/$', 'can_view_all_sales'),
            
            # Products
            (r'^/products/$', 'can_view_products'),
            (r'^/products/\d+/$', 'can_view_products'),
            (r'^/add-product/$', 'can_add_products'),
            (r'^/edit-product/\d+/$', 'can_edit_products'),
            (r'^/toggle-product/\d+/$', 'can_edit_products'),
            (r'^/delete-product/\d+/$', 'can_delete_products'),
            (r'^/import-products/$', 'can_import_products'),
            
            # Inventory
            (r'^/inventory-report/$', 'can_view_inventory'),
            (r'^/stock-management/$', 'can_manage_stock'),
            (r'^/batch-list/$', 'can_view_inventory'),
            (r'^/batch/\d+/$', 'can_view_inventory'),
            (r'^/add-batch/$', 'can_manage_stock'),
            (r'^/edit-batch/\d+/$', 'can_manage_stock'),
            (r'^/delete-batch/\d+/$', 'can_manage_stock'),
            (r'^/stock-journal/$', 'can_manage_stock'),
            
            # Purchases
            (r'^/purchases/$', 'can_view_purchases'),
            (r'^/purchase-list/$', 'can_view_purchases'),
            (r'^/purchase/\d+/$', 'can_view_purchases'),
            (r'^/view-purchase/\d+/$', 'can_view_purchases'),
            (r'^/add-purchase/$', 'can_add_purchases'),
            (r'^/edit-purchase/\d+/$', 'can_edit_purchases'),
            (r'^/delete-purchase/\d+/$', 'can_delete_purchases'),
            (r'^/purchase-invoice/\d+/$', 'can_view_purchases'),
            (r'^/pending-purchases/$', 'can_add_purchases'),
            
            # Customers
            (r'^/customers/$', 'can_view_customers'),
            (r'^/customer/\d+/$', 'can_view_customers'),
            (r'^/customer-detail/\d+/$', 'can_view_customers'),
            (r'^/add-customer/$', 'can_add_customers'),
            (r'^/edit-customer/\d+/$', 'can_edit_customers'),
            (r'^/delete-customer/\d+/$', 'can_delete_customers'),
            
            # Suppliers
            (r'^/suppliers/$', 'can_view_suppliers'),
            (r'^/supplier/\d+/$', 'can_view_suppliers'),
            (r'^/supplier-detail/\d+/$', 'can_view_suppliers'),
            (r'^/add-supplier/$', 'can_add_suppliers'),
            (r'^/edit-supplier/\d+/$', 'can_edit_suppliers'),
            (r'^/delete-supplier/\d+/$', 'can_delete_suppliers'),
            
            # Reports
            (r'^/reports-dashboard/$', 'can_view_reports'),
            (r'^/sales-by-product/$', 'can_view_sales_reports'),
            (r'^/profit-margin-report/$', 'can_view_profit_reports'),
            (r'^/customer-sales-analysis/$', 'can_view_customer_reports'),
            (r'^/export-report/$', 'can_export_reports'),
            (r'^/export/', 'can_export_reports'),
            
            # Financial
            (r'^/credit-payments/$', 'can_view_credit_sales'),
            (r'^/process-credit-payment/$', 'can_process_credit_payments'),
            (r'^/product-level-credit-payment/$', 'can_process_credit_payments'),
            (r'^/refund/', 'can_process_refunds'),
            
            # Expenses
            (r'^/expenses/$', 'can_view_financials'),
            (r'^/add-expense/$', 'can_manage_settings'),
            
            # Admin/User Management
            (r'^/user-management/$', 'can_manage_users'),
            (r'^/users/$', 'can_manage_users'),
            (r'^/user/\d+/$', 'can_manage_users'),
            (r'^/create-user/$', 'can_manage_users'),
            (r'^/edit-user/\d+/$', 'can_manage_users'),
            (r'^/reset-password/\d+/$', 'can_manage_users'),
            (r'^/roles/$', 'can_manage_roles'),
            (r'^/create-role/$', 'can_manage_roles'),
            (r'^/edit-role/\d+/$', 'can_manage_roles'),
            (r'^/company-settings/$', 'can_manage_settings'),
            
            # Activity Logs
            (r'^/activity-logs/$', 'can_manage_users'),
            (r'^/admin/activity-logs/$', 'can_manage_users'),
        ]
        
        # Public URLs that don't require permission checks
        self.public_urls = [
            r'^/login/$',
            r'^/logout/$',
            r'^/static/',
            r'^/media/',
            r'^/password-reset/',
            r'^/password-reset-confirm/',
            r'^/payment-callback/',
            r'^/paystack-webhook/',
            r'^/verify-payment/',
        ]
    
    def __call__(self, request):
        # Skip permission check for public URLs
        for pattern in self.public_urls:
            if re.match(pattern, request.path):
                return self.get_response(request)
        
        # Skip if user is not authenticated (login page will handle)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Superusers bypass all permission checks
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Check if user has a profile with role
        if not hasattr(request.user, 'profile'):
            messages.warning(request, 'Your account is not fully configured. Please contact administrator.')
            return self.get_response(request)
        
        if not request.user.profile.role:
            messages.warning(request, 'No role assigned. Please contact administrator.')
            return self.get_response(request)
        
        # Check if user is active
        if not request.user.is_active or not request.user.profile.is_active:
            messages.error(request, 'Your account is inactive. Please contact administrator.')
            return redirect('custom_login')
        
        # Check permissions for the requested URL
        for pattern, required_permission in self.permission_map:
            if re.match(pattern, request.path):
                if not request.user.profile.has_permission(required_permission):
                    # User doesn't have permission
                    messages.error(request, f'You do not have permission to access this page.')
                    
                    # If it's an AJAX request, return 403
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return HttpResponseForbidden('Permission denied')
                    
                    return redirect('dashboard')
                break
        
        return self.get_response(request)


class RequestLoggingMiddleware:
    """
    Middleware to capture request object for signals and log views
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request in thread local for signals
        from pos.signals import _request_local
        _request_local.request = request
        
        response = self.get_response(request)
        
        # Log view actions for important pages
        if request.user.is_authenticated and request.method == 'GET':
            # Log view actions for detail pages
            path = request.path
            if '/product/' in path or '/customer/' in path or '/supplier/' in path:
                try:
                    # Extract model name and ID from URL
                    parts = path.strip('/').split('/')
                    if len(parts) >= 2:
                        model_name = parts[0].capitalize()
                        object_id = parts[1] if parts[1].isdigit() else None
                        from pos.logger import log_view
                        log_view(request.user, model_name, object_id, request)
                except:
                    pass
        
        return response