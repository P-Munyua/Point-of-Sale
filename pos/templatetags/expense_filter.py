from django import template

register = template.Library()

@register.filter
def dict_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary and key in dictionary:
        return dictionary[key]
    return 0