from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='pprint')
def pprint_filter(value):
    """Pretty print a value"""
    import json
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


@register.filter(name='to_percentage')
def to_percentage(value):
    """Convert a decimal confidence (0-1) to percentage (0-100)"""
    try:
        if value is None:
            return 0
        # If already a percentage (> 1), return as is
        if float(value) > 1:
            return int(float(value))
        # Otherwise convert from 0-1 to 0-100
        return int(float(value) * 100)
    except (TypeError, ValueError):
        return 0
