# pos/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from functools import wraps

def permission_required(permission_name, redirect_url='dashboard', ajax_message='Permission denied'):
    """
    Decorator to check if a user has a specific permission.
    
    Usage:
        @permission_required('can_view_products')
        def product_list(request):
            ...
    
    Args:
        permission_name: The permission to check (e.g., 'can_view_products')
        redirect_url: URL to redirect to if permission is denied
        ajax_message: Message to return for AJAX requests
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Superusers bypass all permission checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to continue.')
                return redirect('custom_login')
            
            # Check if user has a profile
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'Your account is not properly configured.')
                return redirect(redirect_url)
            
            # Check permission
            if not request.user.profile.has_permission(permission_name):
                error_message = f'You do not have permission to perform this action.'
                
                # For AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_message,
                        'permission_required': permission_name
                    }, status=403)
                
                messages.error(request, error_message)
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def role_required(allowed_roles, redirect_url='dashboard'):
    """
    Decorator to check if a user has one of the allowed roles.
    
    Usage:
        @role_required(['admin', 'manager'])
        def admin_dashboard(request):
            ...
    
    Args:
        allowed_roles: List of role names that are allowed
        redirect_url: URL to redirect to if access is denied
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to continue.')
                return redirect('custom_login')
            
            if not hasattr(request.user, 'profile') or not request.user.profile.role:
                messages.error(request, 'No role assigned to your account.')
                return redirect(redirect_url)
            
            role_name = request.user.profile.role.name
            if role_name not in allowed_roles:
                messages.error(request, f'This page is restricted to: {", ".join(allowed_roles)}')
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def login_and_permission_required(permission_name, redirect_url='dashboard'):
    """
    Combines login_required and permission_required in one decorator.
    
    Usage:
        @login_and_permission_required('can_view_products')
        def product_list(request):
            ...
    """
    from django.contrib.auth.decorators import login_required
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            return permission_required(permission_name, redirect_url)(view_func)(request, *args, **kwargs)
        return _wrapped_view
    return decorator