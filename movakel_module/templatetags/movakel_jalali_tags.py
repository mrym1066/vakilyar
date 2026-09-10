# templatetags/jalali_tags.py
from django import template
import jdatetime

register = template.Library()

@register.filter
def to_jalali(date):
    if not date:
        return ''
    try:
        return jdatetime.datetime.fromgregorian(datetime=date).strftime('%Y/%m/%d')
    except:
        return date
