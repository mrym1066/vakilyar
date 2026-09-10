from decimal import Decimal
from django import template

register = template.Library()

@register.filter(name='three_digits_currency')
def three_digits_currency(value):
    if value in (None, ""):
        return "-"

    try:
        if isinstance(value, Decimal):
            number = int(value)
        else:
            number = int(float(value))

        return f"{number:,} تومان"

    except (ValueError, TypeError):
        return "-"