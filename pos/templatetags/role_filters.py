
# pos/templatetags/role_filters.py
from django import template

register = template.Library()

@register.filter
def has_permission(role, field_name):
    """Check if a role has a specific permission"""
    try:
        return getattr(role, field_name, False)
    except:
        return False

@register.filter
def get_field_value(form, field_name):
    """Get field value from form"""
    try:
        return form[field_name].value()
    except:
        return False

@register.filter
def getattr_filter(obj, attr_name):
    """Get attribute from object"""
    try:
        return getattr(obj, attr_name, '')
    except:
        return ''

from django import template



@register.filter
def get_item_or_default(obj, field_name):
    """Get attribute value from object or return False if not found"""
    return getattr(obj, field_name, False)

@register.filter
def get_category_enabled_count(role, category_name):
    """Count enabled permissions in a category for a role"""
    # This should be implemented based on your permission_categories structure
    # You might need to pass permission_categories from the view
    return 0  # Placeholder