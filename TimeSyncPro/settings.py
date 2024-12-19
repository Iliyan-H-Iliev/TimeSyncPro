import os
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv

environment = os.getenv("ENV", "production")

if environment == "production":
    load_dotenv(dotenv_path=".env.production")
else:
    load_dotenv(dotenv_path=".env.development")

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG") == "True"

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

handler403 = "TimeSyncPro.common.views.custom_403"
handler404 = "TimeSyncPro.common.views.custom_404"

INTERNAL_IPS = [
    "127.0.0.1",
]

AUTHENTICATION_BACKENDS = [
    "TimeSyncPro.accounts.backends.CaseInsensitiveEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_celery_beat",
    "storages",
    "debug_toolbar",
    "widget_tweaks",
    "celery",
    "TimeSyncPro.absences.apps.AbsencesConfig",
    "TimeSyncPro.accounts.apps.AccountsConfig",
    "TimeSyncPro.common.apps.CommonConfig",
    "TimeSyncPro.companies.apps.CompaniesConfig",
    "TimeSyncPro.history.apps.HistoryConfig",
    "TimeSyncPro.reports.apps.ReportsConfig",
    "TimeSyncPro.shifts.apps.ShiftsConfig",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "TimeSyncPro.middleware.check_company_middleware.CompanyCheckMiddleware",
    "TimeSyncPro.middleware.history_user_middleware.HistoryUserMiddleware",
]

ROOT_URLCONF = os.getenv("ROOT_URLCONF")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = os.getenv("WSGI_APPLICATION")
ASGI_APPLICATION = os.getenv("ASGI_APPLICATION")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv(
            "DB_NAME",
        ),
        "USER": os.getenv(
            "DB_USER",
        ),
        "PASSWORD": os.getenv(
            "DB_PASSWORD",
        ),
        "HOST": os.getenv(
            "DB_HOST",
        ),
        "PORT": os.getenv(
            "DB_PORT",
        ),
    }
}

LOGOUT_REDIRECT_URL = os.getenv("LOGOUT_REDIRECT_URL")
LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL")
LOGIN_URL = os.getenv("LOGIN_URL")


# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_KEY')
#
# AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
# AWS_S3_OBJECT_PARAMETERS = False
# AWS_S3_REGION_NAME = 'eu-north-1'
# AWS_DEFAULT_ACL = 'public-read'
# AWS_QUERYSTRING_AUTH = False
#
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

STORAGE = (
    {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "static": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
    },
)


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

if DEBUG:
    AUTH_PASSWORD_VALIDATORS = []

# Internationalization
DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE")
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE")
TIME_ZONE = os.getenv("TIME_ZONE")
USE_I18N = os.getenv("USE_I18N") == "True"
USE_L10N = os.getenv("USE_L10N") == "True"
USE_TZ = os.getenv("USE_TZ") == "True"


USE_S3 = os.getenv("USE_S3") == "True"

# if USE_S3:
# aws settings
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_DEFAULT_ACL = None
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "eu-north-1")
AWS_S3_CUSTOM_DOMAIN = "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}


# TODO: S3 static settings
# s3 static settings
# STATIC_LOCATION = 'static'
# STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# STATICFILES_DIRS = (BASE_DIR / 'staticfiles',)

# s3 public media settings
PUBLIC_MEDIA_LOCATION = "media"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# else:
#     STATIC_URL = '/static/'
#     STATIC_ROOT = os.path.join(BASE_DIR, 'static')
#     # MEDIA_URL = '/media/'
#     # MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_URL = os.getenv("STATIC_URL")
STATIC_ROOT = os.getenv("STATIC_ROOT")
STATICFILES_DIRS = (BASE_DIR / "staticfiles",)
#
#     # Media files
# MEDIA_URL = os.getenv('MEDIA_URL')
# MEDIA_ROOT = os.getenv('MEDIA_ROOT')

# Static files (CSS, JavaScript, Images)


# Default primary key field type
DEFAULT_AUTO_FIELD = os.getenv("DEFAULT_AUTO_FIELD")

# Custom user model
AUTH_USER_MODEL = 'accounts.TSPUser'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",
        },
    },
}

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

CELERY_BEAT_SCHEDULE = {
    "generate-shift-dates": {
        "task": "TimeSyncPro.shifts.tasks.generate_shift_dates_for_next_year",
        "schedule": crontab(month_of_year="1", day_of_month="1", hour="0", minute="5"),
    },
    "yearly-leave-days-update": {
        "task": "TimeSyncPro.companies.tasks.yearly_set_next_year_leave_days",
        "schedule": crontab(month_of_year="1", day_of_month="1", hour="1", minute="0"),
    },
    # "print-some-text": {
    #     "task": "TimeSyncPro.companies.tasks.print_some_text",
    #     "schedule": crontab(minute="*/1"),
    # },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
