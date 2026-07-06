from django import template

register = template.Library()

@register.filter(name='get_item_or_default')
def get_item_or_default(value, arg):
    """
    Get a value from a dictionary or return default.
    Usage: {{ dict|get_item_or_default:key }}
    """
    if hasattr(value, 'get'):
        return value.get(arg, False)
    return False

@register.filter
def get_field(form, field_name):
    """Get form field by name"""
    if hasattr(form, 'fields') and field_name in form.fields:
        return form[field_name]
    return None

@register.filter
def get_field_value(form, field_name):
    """Get form field value by name"""
    if hasattr(form, 'cleaned_data') and field_name in form.cleaned_data:
        return form.cleaned_data.get(field_name)
    elif hasattr(form, 'initial') and field_name in form.initial:
        return form.initial.get(field_name)
    elif hasattr(form, 'data') and field_name in form.data:
        return form.data.get(field_name)
    return False