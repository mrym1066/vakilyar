from datetime import datetime, date

def _to_date(value):
    """
    فرم DamageCalculationForm مقدار due_date/payment_date را به‌صورت
    آبجکت date واقعی برمی‌گرداند (نه رشته)، بنابراین این تابع هر دو حالت
    را می‌پذیرد تا تابع هم از فرم و هم مستقیم (با رشته) قابل فراخوانی باشد.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def calculate_damage(original_amount, due_date, payment_date, inflation_rate):
    """
    محاسبه خسارت تأخیر تأدیه
    """
    due_date = _to_date(due_date)
    payment_date = _to_date(payment_date)

    if payment_date <= due_date:
        return 0  # اگر بدهی سر وقت پرداخت شود، خسارتی ندارد

    # محاسبه تعداد روزهای تأخیر
    delay_days = (payment_date - due_date).days
    
    # محاسبه خسارت بر اساس فرمول
    damage = original_amount * (1 + (inflation_rate / 100) * (delay_days / 365))
    return round(damage, 2)
