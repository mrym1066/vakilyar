from django import template
from jalali_date import datetime2jalali
from jalali_date import date2jalali
import jdatetime

register = template.Library()

# تاریخ با فرمت کامل مثل "۱۷ فروردین ۱۴۰۴"
@register.filter
def jalali_date(value):
    if not value:
        return ''
    
    j_date = datetime2jalali(value) if hasattr(value, 'hour') else date2jalali(value)
    
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    day = j_date.day
    month_name = months[j_date.month - 1]
    year = j_date.year
    return f"{day} {month_name} {year}"

@register.filter(name='jdate')
def jdate(value):
    return jalali_date(value)
