# pos/templatetags/permission_tags.py
from django import template
from django.contrib.auth.models import AnonymousUser

register = template.Library()

@register.filter
def has_perm(user, permission_name):
    """Check if a user has a specific permission."""
    if not user or isinstance(user, AnonymousUser):
        return False
    
    if user.is_superuser:
        return True
    
    if not hasattr(user, 'profile'):
        return False
    
    return user.profile.has_permission(permission_name)


@register.filter
def user_role(user):
    """Get the user's role display name."""
    if not user or isinstance(user, AnonymousUser):
        return 'Anonymous'
    
    if not hasattr(user, 'profile') or not user.profile.role:
        return 'No Role'
    
    return user.profile.role.get_name_display()


@register.simple_tag(takes_context=True)
def check_permission(context, permission_name):
    """Check permission in template context."""
    request = context.get('request')
    if not request or not request.user:
        return False
    
    if request.user.is_superuser:
        return True
    
    if not hasattr(request.user, 'profile'):
        return False
    
    return request.user.profile.has_permission(permission_name)