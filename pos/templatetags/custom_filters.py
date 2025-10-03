from django import template

register = template.Library()

@register.filter(name='expense_badge_color')
def expense_badge_color(category):
    color_map = {
        'rent': 'primary',
        'salaries': 'success',
        'utilities': 'info',
        'transport': 'warning',
        'other': 'danger'
    }
    return color_map.get(category, 'secondary')


from django import template

register = template.Library()

@register.filter
def sum_attribute(queryset, attr):
    return sum(getattr(item, attr, 0) for item in queryset)

@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0
    

from django import template

register = template.Library()

@register.filter
def sum_attribute(queryset, attr):
    """Sum a specific attribute from a list of objects"""
    return sum(getattr(item, attr, 0) for item in queryset)

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage of value from total"""
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, ZeroDivisionError):
        return 0