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


from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        if arg:
            if isinstance(value, (int, float, Decimal)) and isinstance(arg, (int, float, Decimal)):
                return float(value) / float(arg)
            return 0
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        if isinstance(value, (int, float, Decimal)) and isinstance(arg, (int, float, Decimal)):
            return float(value) * float(arg)
        return 0
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg=100):
    """Calculate percentage: (value/arg)*100"""
    try:
        if arg:
            if isinstance(value, (int, float, Decimal)) and isinstance(arg, (int, float, Decimal)):
                return (float(value) / float(arg)) * 100
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        if isinstance(value, (int, float, Decimal)) and isinstance(arg, (int, float, Decimal)):
            return float(value) - float(arg)
        return value
    except (ValueError, TypeError):
        return value

@register.filter
def add(value, arg):
    """Add arg to value"""
    try:
        if isinstance(value, (int, float, Decimal)) and isinstance(arg, (int, float, Decimal)):
            return float(value) + float(arg)
        return value
    except (ValueError, TypeError):
        return value

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.filter
def format_currency(value):
    """Format value as currency"""
    try:
        return f"KSh {float(value):,.2f}"
    except (ValueError, TypeError):
        return f"KSh 0.00"

@register.filter
def calculate_margin(sales, cost):
    """Calculate profit margin: ((sales-cost)/sales)*100"""
    try:
        if sales:
            margin = ((float(sales) - float(cost)) / float(sales)) * 100
            return round(margin, 2)
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0











from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        if arg and value:
            # Convert to float for division
            value_float = float(value) if not isinstance(value, float) else value
            arg_float = float(arg) if not isinstance(arg, float) else arg
            return value_float / arg_float
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        if value is not None and arg is not None:
            # Convert to float for multiplication
            value_float = float(value) if not isinstance(value, float) else value
            arg_float = float(arg) if not isinstance(arg, float) else arg
            return value_float * arg_float
        return 0
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        if value is not None and arg is not None:
            value_float = float(value) if not isinstance(value, float) else value
            arg_float = float(arg) if not isinstance(arg, float) else arg
            return value_float - arg_float
        return value
    except (ValueError, TypeError):
        return value

@register.filter
def add(value, arg):
    """Add arg to value"""
    try:
        if value is not None and arg is not None:
            value_float = float(value) if not isinstance(value, float) else value
            arg_float = float(arg) if not isinstance(arg, float) else arg
            return value_float + arg_float
        return value
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value, total=100):
    """Calculate percentage: (value/total)*100"""
    try:
        if total and value is not None:
            value_float = float(value) if not isinstance(value, float) else value
            total_float = float(total) if not isinstance(total, float) else total
            return (value_float / total_float) * 100
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def calculate_percentage(value, total):
    """Alias for percentage filter"""
    return percentage(value, total)

@register.filter
def format_currency(value):
    """Format value as currency"""
    try:
        if value is not None:
            return f"KSh {float(value):,.2f}"
        return "KSh 0.00"
    except (ValueError, TypeError):
        return "KSh 0.00"

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

@register.filter
def is_greater_than(value, arg):
    """Check if value is greater than arg"""
    try:
        return float(value) > float(arg)
    except (ValueError, TypeError):
        return False

@register.filter
def is_less_than(value, arg):
    """Check if value is less than arg"""
    try:
        return float(value) < float(arg)
    except (ValueError, TypeError):
        return False


