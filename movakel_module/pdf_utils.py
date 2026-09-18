"""
ابزارهای تولید PDF برای سامانه وکیل‌یار
با استفاده از xhtml2pdf + arabic_reshaper + bidi
"""
import os
import re
from io import BytesIO

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

import jdatetime

try:
    from xhtml2pdf import pisa
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False


# ═══════════════════════════════════════════════════════════
# ثبت فونت فارسی
# ═══════════════════════════════════════════════════════════
_FONTS_REGISTERED = False


def _get_font_path(filename):
    """مسیر فونت رو در چندین محل ممکن چک می‌کنه"""
    candidates = [
        os.path.join(settings.BASE_DIR, 'static', 'fonts', filename),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', filename),
        os.path.join(settings.BASE_DIR, 'movakel_module', 'static', 'fonts', filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _register_fonts():
    """ثبت فونت فارسی برای xhtml2pdf"""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED or not XHTML2PDF_AVAILABLE:
        return

    fonts = [
        ('IRANSans', 'IRANSans.ttf'),
        ('IRANSans-Bold', 'IRANSansWeb_Bold.ttf'),
    ]

    for font_name, filename in fonts:
        path = _get_font_path(filename)
        if path:
            try:
                pdfmetrics.registerFont(TTFont(font_name, path))
                print(f"✅ فونت ثبت شد: {font_name} → {path}")
            except Exception as e:
                print(f"❌ خطا در ثبت {font_name}: {e}")
        else:
            print(f"❌ فونت یافت نشد: {filename}")

    _FONTS_REGISTERED = True


# ═══════════════════════════════════════════════════════════
# تابع Reshape برای متن‌های فارسی
# ═══════════════════════════════════════════════════════════
def _reshape_text(text):
    """تبدیل متن فارسی به شکل صحیح برای PDF"""
    if not BIDI_AVAILABLE or not text:
        return text

    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return text


def _reshape_html_content(html):
    """
    Reshape کردن متن‌های فارسی داخل HTML
    فقط متن‌های داخل تگ‌ها رو reshape می‌کنه، نه خود تگ‌ها رو
    """
    if not BIDI_AVAILABLE:
        return html

    # الگو: پیدا کردن متن بین > و <
    def reshape_match(match):
        text = match.group(1)
        # اگه متن خالی یا فقط فاصله/عدد باشه، دست نزن
        if not text.strip():
            return match.group(0)
        # اگه فقط عدد و علائم باشه، دست نزن
        if re.match(r'^[\d\s\.\,\:\/\-\(\)]+$', text.strip()):
            return match.group(0)
        # reshape کن
        reshaped = arabic_reshaper.reshape(text)
        reshaped = get_display(reshaped)
        return '>' + reshaped + '<'

    # فقط متن‌های بین تگ‌ها رو reshape کن
    html = re.sub(r'>([^<>]+)<', reshape_match, html)
    return html


# ═══════════════════════════════════════════════════════════
# Link Callback
# ═══════════════════════════════════════════════════════════
def link_callback(uri, rel):
    """resolve کردن منابع برای xhtml2pdf"""
    if not uri.startswith(('/', 'http://', 'https://')):
        font_path = _get_font_path(uri)
        if font_path:
            return font_path

    if uri.startswith('/static/'):
        path = os.path.join(settings.BASE_DIR, 'static', uri[8:])
        if os.path.exists(path):
            return path

    if uri.startswith(('http://', 'https://')):
        return uri

    if os.path.isabs(uri) and os.path.exists(uri):
        return uri

    return os.path.join(settings.BASE_DIR, 'static', uri.lstrip('/'))


# ═══════════════════════════════════════════════════════════
# تابع اصلی: HTML → PDF
# ═══════════════════════════════════════════════════════════
def render_to_pdf(template_name, context, request=None):
    """تبدیل قالب HTML به PDF"""
    if not XHTML2PDF_AVAILABLE:
        raise ImportError("xhtml2pdf نصب نیست")

    _register_fonts()

    # رندر HTML
    html_string = render_to_string(template_name, context, request=request)

    # ═══ Bidi رو کاملاً غیرفعال کن ═══
    # html_string = _reshape_html_content(html_string)  ← این خط رو کامنت کن

    # تزریق فونت به HTML
    font_path = _get_font_path('IRANSans.ttf')
    font_css = f"""
        <style>
            @font-face {{
                font-family: IRANSans;
                src: url("{font_path}");
            }}
            * {{
                font-family: IRANSans !important;
            }}
            body {{
                font-family: IRANSans !important;
                direction: rtl;
                text-align: right;
            }}
        </style>
    """

    if '</head>' in html_string:
        html_string = html_string.replace('</head>', font_css + '</head>')
    else:
        html_string = font_css + html_string

    # تبدیل به PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(
        BytesIO(html_string.encode('utf-8')),
        result,
        encoding='utf-8',
        link_callback=link_callback,
    )

    if pdf.err:
        print(f"❌ خطای pisaDocument: {pdf.err}")
        return None

    result.seek(0)
    return result
# ═══════════════════════════════════════════════════════════
# Context مشترک
# ═══════════════════════════════════════════════════════════
def get_common_pdf_context():
    """context مشترک برای همه PDFها"""
    from site_module.models import SiteSetting

    print_date = jdatetime.date.fromgregorian(
        date=timezone.now().date()
    ).strftime('%Y/%m/%d')

    return {
        'site_setting': SiteSetting.objects.filter(is_main_setting=True).first(),
        'print_date': print_date,
    }


# ═══════════════════════════════════════════════════════════
# Helper: نام فایل امن
# ═══════════════════════════════════════════════════════════
def safe_pdf_filename(prefix, name, extension='pdf'):
    """ساخت نام فایل امن برای دانلود"""
    safe = re.sub(r'[^\w\u0600-\u06FF\s-]', '', str(name or ''))
    safe = safe.strip().replace(' ', '_')
    safe = safe[:50] or 'document'

    return f"{prefix}_{safe}.{extension}"