from datetime import datetime

def calculate_damage(original_amount, due_date, payment_date, inflation_rate):
    """
    محاسبه خسارت تأخیر تأدیه
    """
    due_date = datetime.strptime(due_date, "%Y-%m-%d")
    payment_date = datetime.strptime(payment_date, "%Y-%m-%d")
    
    if payment_date <= due_date:
        return 0  # اگر بدهی سر وقت پرداخت شود، خسارتی ندارد

    # محاسبه تعداد روزهای تأخیر
    delay_days = (payment_date - due_date).days
    
    # محاسبه خسارت بر اساس فرمول
    damage = original_amount * (1 + (inflation_rate / 100) * (delay_days / 365))
    return round(damage, 2)
