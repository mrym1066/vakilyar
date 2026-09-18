from datetime import date

from django.test import TestCase

from .models import Movakel
from .utils import calculate_damage


class CalculateDamageTests(TestCase):
    """
    تست تابع محاسبه خسارت تأخیر تأدیه (utils.calculate_damage).
    این تست‌ها به‌خصوص برای جلوگیری از بازگشت باگ قبلی نوشته شده‌اند:
    فرم DamageCalculationForm مقدار date واقعی برمی‌گرداند نه رشته، و تابع
    قبلاً روی آن کرش می‌کرد.
    """

    def test_accepts_date_objects_like_the_real_form(self):
        result = calculate_damage(10_000_000, date(2024, 1, 1), date(2024, 6, 1), 40)
        self.assertGreater(result, 10_000_000)

    def test_still_accepts_string_dates(self):
        result_from_dates = calculate_damage(10_000_000, date(2024, 1, 1), date(2024, 6, 1), 40)
        result_from_strings = calculate_damage(10_000_000, '2024-01-01', '2024-06-01', 40)
        self.assertEqual(result_from_dates, result_from_strings)

    def test_no_delay_means_no_damage(self):
        self.assertEqual(calculate_damage(10_000_000, date(2024, 1, 1), date(2024, 1, 1), 40), 0)
        self.assertEqual(calculate_damage(10_000_000, date(2024, 6, 1), date(2024, 1, 1), 40), 0)


class MovakelTaxCalculationTests(TestCase):
    """تست محاسبات مالیاتی مدل Movakel (تمبر، سهم کانون، مالیات سالانه)"""

    def setUp(self):
        self.movakel = Movakel.objects.create(
            name='آزمایشی',
            age='30',
            mobile_number='09120000000',
            description='پرونده تستی',
            total_amount=100_000_000,
        )

    def test_stamp_tax_is_five_percent(self):
        self.assertEqual(self.movakel.stamp_tax(), 5_000_000)

    def test_judiciary_share_is_five_percent(self):
        self.assertEqual(self.movakel.judiciary_share(), 5_000_000)

    def test_annual_tax_is_twenty_five_percent(self):
        self.assertEqual(self.movakel.annual_tax(), 25_000_000)

    def test_total_tax_is_sum_of_all_components(self):
        self.assertEqual(
            self.movakel.total_tax(),
            self.movakel.stamp_tax() + self.movakel.judiciary_share() + self.movakel.annual_tax(),
        )


class MovakelSlugUniquenessTests(TestCase):
    """
    رگرسیون برای باگ حلقه بی‌پایان تولید slug: دو موکل هم‌نام باید
    اسلاگ‌های متفاوت بگیرند و ساخت هیچ‌کدام نباید گیر کند/کرش کند.
    """

    def test_duplicate_names_get_unique_slugs(self):
        m1 = Movakel.objects.create(
            name='علی محمدی', age='25', mobile_number='09121111111',
            description='پرونده اول', total_amount=0,
        )
        m2 = Movakel.objects.create(
            name='علی محمدی', age='25', mobile_number='09122222222',
            description='پرونده دوم', total_amount=0,
        )
        self.assertTrue(m1.slug)
        self.assertTrue(m2.slug)
        self.assertNotEqual(m1.slug, m2.slug)
