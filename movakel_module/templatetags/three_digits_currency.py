from django import template

register = template.Library()

@register.filter
def three_digits_currency(value):
    try:
        # اطمینان حاصل کنید که مقدار عدد است
        value = float(value)
        # جدا کردن سه رقم و افزودن "تومان"
        return "{:,.0f} تومان".format(value)
    except (ValueError, TypeError):
        return "0 تومان"

@register.filter
def persian_intcomma(value):
    try:
        value = float(value)
        return "{:,.0f}".format(value)
    except (ValueError, TypeError):
        return "0"