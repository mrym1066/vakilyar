"""
Vakilyar - common template tags and filters
"""
from decimal import Decimal
from django import template
import jdatetime
from jalali_date import datetime2jalali, date2jalali

register = template.Library()


# ===== Jalali Date Filters =====

@register.filter(name='jalali_date')
def jalali_date(value):
    if not value:
        return ''
    try:
        j_date = datetime2jalali(value) if hasattr(value, 'hour') else date2jalali(value)
        months = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        day = j_date.day
        month_name = months[j_date.month - 1]
        year = j_date.year
        return f"{day} {month_name} {year}"
    except Exception:
        return value


@register.filter(name='jdate')
def jdate(value):
    return jalali_date(value)


@register.filter(name='to_jalali')
def to_jalali(date, fmt='%Y/%m/%d'):
    """
    Convert Gregorian date to Jalali
    Works with both 1 or 2 arguments:
    - {{ date|to_jalali }} -> default format
    - {{ date|to_jalali:"%Y/%m/%d" }} -> custom format
    """
    if not date:
        return ''
    try:
        return jdatetime.datetime.fromgregorian(datetime=date).strftime(fmt)
    except Exception:
        try:
            return jdatetime.date.fromgregorian(date=date).strftime(fmt)
        except Exception:
            return str(date) if date else ''


# ===== Currency and Number Filters =====

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


@register.filter(name='persian_intcomma')
def persian_intcomma(value):
    try:
        value = float(value)
        return "{:,.0f}".format(value)
    except (ValueError, TypeError):
        return "0"


@register.filter(name='intcomma_fa')
def intcomma_fa(value):
    return persian_intcomma(value)