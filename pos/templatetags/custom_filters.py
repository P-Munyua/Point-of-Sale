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