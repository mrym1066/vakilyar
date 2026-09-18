from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# ===================== امنیت =====================
# SECRET_KEY از فایل .env خوانده می‌شود.
# اگر .env وجود نداشت (مثلاً اولین بار نصب)، مقدار پیش‌فرض زیر استفاده می‌شود.
# برای نصب روی هر سیستم جدید، یک فایل .env با SECRET_KEY اختصاصی بسازید.
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'Pnd9Q7KG6d7RL1dnX9w1NuT3dfsXYe3wB0hfQCbrzlQUPBsGE6st0b6A4F60mWB5Xf8'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# برای نصب روی شبکه محلی (LAN)، IP دستگاه سرور را اینجا اضافه کنید
# مثال: ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.10']
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS', 'localhost,127.0.0.1'
).split(',')


INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # اپ‌های داخلی
    'account_module',
    'movakel_module',
    'contact_module',
    'site_module',
    'user_panel_module',
    'admin_panel',
    'article_module',
    'polls',
    # اپ‌های خارجی
    'django_render_partial',
    'sorl.thumbnail',
    'jalali_date',
    'django_jalali',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vakilyar_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'site_module.context_processors.site_setting',
            ],
        },
    },
]

WSGI_APPLICATION = 'vakilyar_project.wsgi.application'

AUTH_USER_MODEL = 'account_module.User'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/movakels/'
LOGOUT_REDIRECT_URL = '/login/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fa-IR'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_ROOT = BASE_DIR / 'uploads'
MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ایمیل — از .env خوانده می‌شود
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_PORT = 587

# Logging
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'vakilyar.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'movakel_module': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Messages
from django.contrib.messages import constants as messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_TAGS = {
    messages.SUCCESS: 'alert-success',
    messages.INFO:    'alert-info',
    messages.WARNING: 'alert-warning',
    messages.ERROR:   'alert-danger',
}

# Jalali
JALALI_DATE_DEFAULTS = {
    'Strftime': {
        'date': '%Y/%m/%d',
        'datetime': '%Y/%m/%d %H:%M',
    },
    'Static': {
        'js': [],
        'css': {
            'all': [
                'admin_panel/jquery.ui.datepicker.jalali/themes/base/jquery-ui.min.css',
            ]
        }
    },
}

JAZZMIN_SETTINGS = {
    "site_title": "وکیل‌یار",
    "site_header": "وکیل‌یار",
    "site_brand": "⚖ وکیل‌یار",
    "site_logo": None,
    "login_logo": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "به پنل مدیریت وکیل‌یار خوش آمدید",
    "copyright": "وکیل‌یار — سامانه مدیریت دفاتر وکالت",
    "search_model": [],
    "user_avatar": None,
    "language_chooser": False,
    "topmenu_links": [
        {"name": "🏠 صفحه اصلی سایت", "url": "/", "new_window": True},
        {"name": "📁 پرونده‌ها", "url": "/movakels/", "new_window": False},
        {"name": "📅 ملاقات‌ها", "url": "/movakels/meetings/", "new_window": False},
    ],
    "usermenu_links": [
        {"name": " مشاهده سایت", "url": "/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": False,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "movakel_module",
        "auth",
        "article_module",
        "contact_module",
        "site_module",
    ],
    "icons": {
        "auth":                              "fas fa-shield-alt",
        "auth.user":                         "fas fa-user-tie",
        "auth.group":                        "fas fa-users",
        "movakel_module":                    "fas fa-balance-scale",
        "movakel_module.movakel":            "fas fa-folder-open",
        "movakel_module.requestmeeting":     "fas fa-calendar-check",
        "movakel_module.movakelpayment":     "fas fa-money-bill-wave",
        "movakel_module.installmentpayment": "fas fa-receipt",
        "movakel_module.action":             "fas fa-tasks",
        "movakel_module.defensedocument":    "fas fa-file-alt",
        "movakel_module.pdffile":            "fas fa-file-pdf",
        "movakel_module.branch":             "fas fa-landmark",
        "movakel_module.meetingtopic":       "fas fa-comments",
        "movakel_module.servicetype":        "fas fa-concierge-bell",
        "movakel_module.visit":              "fas fa-handshake",
        "article_module":                    "fas fa-newspaper",
        "article_module.article":            "fas fa-pen-fancy",
        "article_module.articlecategory":    "fas fa-tags",
        "contact_module":                    "fas fa-envelope-open-text",
        "contact_module.contactus":          "fas fa-envelope",
        "site_module":                       "fas fa-cog",
        "site_module.sitesetting":           "fas fa-sliders-h",
    },
    "default_icon_parents":  "fas fa-chevron-circle-left",
    "default_icon_children": "fas fa-dot-circle",
    "related_modal_active": True,
    "custom_css":           "css/jazzmin_custom.css",
    "custom_js":            "js/sidebar_mobile.js",
    "use_google_fonts_cdn": True,
    "show_ui_builder":      False,
    "custom_links": {},
    "dashboard_plus": True,
    "show_recent_actions": True,
    "recent_actions_limit": 10,
    "changeform_format":    "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user":  "collapsible",
        "auth.group": "vertical_tabs",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":  False,
    "footer_small_text":  False,
    "body_small_text":    False,
    "brand_small_text":   False,
    "brand_colour":   "navbar-primary",
    "accent":         "accent-warning",
    "navbar":         "navbar-dark navbar-primary",
    "no_navbar_border": True,
    "navbar_fixed":   True,
    "layout_boxed":  False,
    "footer_fixed":  False,
    "sidebar_fixed":              False,
    "sidebar":                    "sidebar-dark-primary",
    "sidebar_nav_small_text":     False,
    "sidebar_disable_expand":     False,
    "sidebar_nav_child_indent":   True,
    "sidebar_nav_compact_style":  True,
    "sidebar_nav_legacy_style":   False,
    "sidebar_nav_flat_style":     False,
    "theme":           "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-outline-secondary",
        "info":      "btn-outline-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
    "actions_sticky_top": True,
}
