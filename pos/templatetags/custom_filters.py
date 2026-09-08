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


from django import template
from datetime import timedelta



@register.filter
def add_days(date, days):
    """Add days to a date"""
    try:
        return date + timedelta(days=int(days))
    except:
        return date

@register.filter
def replace(date, **kwargs):
    """Replace parts of a date (used in template)"""
    return date  # This is simplified - you might need actual date replacement logic


# pos/templatetags/math_filters.py
from django import template



@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

# pos/templatetags/math_filters.py
from django import template
from decimal import Decimal


@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except:
        try:
            return float(value) * float(arg)
        except (ValueError, TypeError):
            return 0

@register.filter
def divide(value, arg):
    """Divide the value by the argument."""
    try:
        return Decimal(str(value)) / Decimal(str(arg))
    except:
        try:
            return float(value) / float(arg) if float(arg) != 0 else 0
        except (ValueError, TypeError, ZeroDivisionError):
            return 0

@register.filter
def add(value, arg):
    """Add the argument to the value."""
    try:
        return Decimal(str(value)) + Decimal(str(arg))
    except:
        try:
            return float(value) + float(arg)
        except (ValueError, TypeError):
            return value

@register.filter
def subtract(value, arg):
    """Subtract the argument from the value."""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except:
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return value

@register.filter
def percentage(value, arg):
    """Calculate percentage: value is what percent of arg?"""
    try:
        if float(arg) != 0:
            return (float(value) / float(arg)) * 100
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


# custom_filters.py
from django import template



@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter
def divide(value, arg):
    """Divide the value by the arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the arg"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0




# pos/templatetags/custom_filters.py
from django import template
from django.db.models import Q



@register.filter
def get_field_value(form, field_name):
    """Get value from form field"""
    if hasattr(form, 'cleaned_data') and field_name in form.cleaned_data:
        return form.cleaned_data[field_name]
    if hasattr(form, 'initial') and field_name in form.initial:
        return form.initial[field_name]
    if hasattr(form, 'instance') and hasattr(form.instance, field_name):
        return getattr(form.instance, field_name)
    return False

@register.filter
def has_permission(role, permission_name):
    """Check if role has specific permission"""
    try:
        return getattr(role, permission_name, False)
    except:
        return False

@register.filter
def get_attr(obj, attr_name):
    """Get attribute from object"""
    try:
        return getattr(obj, attr_name, '')
    except:
        return ''

@register.filter
def permission_count(permission_matrix, field_name):
    """Count how many roles have a specific permission"""
    if not permission_matrix:
        return 0
    
    count = 0
    for item in permission_matrix:
        if isinstance(item, dict) and 'role' in item:
            role = item['role']
            if hasattr(role, field_name) and getattr(role, field_name, False):
                count += 1
    return count

# FIXED: Use @register.simple_tag without assignment syntax
@register.simple_tag
def get_permission_categories():
    """Get permission categories"""
    return {
        'Dashboard & POS': [
            ('can_access_dashboard', 'Access Dashboard'),
            ('can_access_pos', 'Access POS Interface'),
            ('can_process_sales', 'Process Sales'),
            ('can_edit_sales', 'Edit Sales'),
            ('can_delete_sales', 'Delete Sales'),
            ('can_view_all_sales', 'View All Sales'),
            ('can_view_own_sales', 'View Own Sales'),
        ],
        'Products Management': [
            ('can_view_products', 'View Products'),
            ('can_add_products', 'Add Products'),
            ('can_edit_products', 'Edit Products'),
            ('can_delete_products', 'Delete Products'),
            ('can_import_products', 'Import Products'),
        ],
        'Inventory Management': [
            ('can_view_inventory', 'View Inventory'),
            ('can_manage_stock', 'Manage Stock'),
            ('can_view_reports', 'View Reports'),
        ],
        'Purchases Management': [
            ('can_view_purchases', 'View Purchases'),
            ('can_add_purchases', 'Add Purchases'),
            ('can_edit_purchases', 'Edit Purchases'),
            ('can_delete_purchases', 'Delete Purchases'),
        ],
        'Customers Management': [
            ('can_view_customers', 'View Customers'),
            ('can_add_customers', 'Add Customers'),
            ('can_edit_customers', 'Edit Customers'),
            ('can_delete_customers', 'Delete Customers'),
        ],
        'Suppliers Management': [
            ('can_view_suppliers', 'View Suppliers'),
            ('can_add_suppliers', 'Add Suppliers'),
            ('can_edit_suppliers', 'Edit Suppliers'),
            ('can_delete_suppliers', 'Delete Suppliers'),
        ],
        'Reports & Analytics': [
            ('can_view_sales_reports', 'View Sales Reports'),
            ('can_view_inventory_reports', 'View Inventory Reports'),
            ('can_view_profit_reports', 'View Profit Reports'),
            ('can_view_customer_reports', 'View Customer Reports'),
            ('can_export_reports', 'Export Reports'),
        ],
        'Financial Management': [
            ('can_view_financials', 'View Financials'),
            ('can_process_refunds', 'Process Refunds'),
            ('can_view_credit_sales', 'View Credit Sales'),
            ('can_process_credit_payments', 'Process Credit Payments'),
        ],
        'System Settings': [
            ('can_manage_settings', 'Manage Settings'),
            ('can_manage_users', 'Manage Users'),
            ('can_manage_roles', 'Manage Roles'),
        ],
    }



from django import template



@register.filter
def get_item(obj, key):
    """
    Get item from object. Works with:
    - Dictionaries: obj.get(key)
    - Objects: getattr(obj, key, None)
    - Lists/Tuples: obj[key] if index exists
    - Forms: obj[key] or getattr(obj, key, None)
    """
    try:
        # Try dictionary-like objects
        if hasattr(obj, 'get'):
            return obj.get(key)
    except AttributeError:
        pass
    
    try:
        # Try object attribute
        return getattr(obj, key, None)
    except AttributeError:
        pass
    
    try:
        # Try index access (lists, tuples)
        return obj[key]
    except (TypeError, IndexError, KeyError):
        return None

@register.filter
def get_field_value(obj, field_name):
    """Get attribute value from object or return False if not found"""
    # First try to get as attribute
    value = getattr(obj, field_name, None)
    
    # If that doesn't work, try as dictionary key
    if value is None and hasattr(obj, '__getitem__'):
        try:
            value = obj.get(field_name, False) if hasattr(obj, 'get') else False
        except (AttributeError, KeyError):
            value = False
    
    # Convert to boolean for permission checks
    if isinstance(value, bool):
        return value
    return bool(value)

@register.filter
def form_field_value(form, field_name):
    """Get field value from a form instance"""
    try:
        # For bound forms
        if hasattr(form, 'cleaned_data'):
            return form.cleaned_data.get(field_name)
        
        # For unbound forms or initial data
        if hasattr(form, 'initial'):
            return form.initial.get(field_name)
        
        # Try direct field access
        field = form.fields.get(field_name)
        if field:
            return field.initial
        
        return None
    except (AttributeError, KeyError):
        return None

@register.filter
def is_checked(form, field_name):
    """Check if a checkbox/boolean field is checked in a form"""
    try:
        # For bound forms
        if form.is_bound:
            return form.data.get(field_name) == 'on' or form.data.get(field_name) == 'true'
        
        # For unbound forms with initial data
        if hasattr(form, 'initial'):
            return bool(form.initial.get(field_name, False))
        
        return False
    except (AttributeError, KeyError):
        return False

# pos/templatetags/custom_filters.py
from django import template
from datetime import datetime, timedelta
from django.utils import timezone



@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def timesince_in_days(value):
    """Calculate days since a datetime"""
    if not value:
        return 0
    try:
        delta = timezone.now() - value
        return delta.days
    except:
        return 0

@register.filter
def add_days(value, days):
    """Add days to a date"""
    try:
        return value + timedelta(days=int(days))
    except:
        return value

@register.filter
def format_currency(value):
    """Format value as currency"""
    try:
        return f"KES {float(value):,.2f}"
    except:
        return "KES 0.00"

@register.filter
def progress_percentage(value, total):
    """Calculate progress percentage"""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except:
        return 0




from django import template



@register.filter
def get_field_value(obj, field_name):
    """Get attribute value from object"""
    return getattr(obj, field_name, False)


