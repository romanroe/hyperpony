import os
import sys
from pathlib import Path


#######################################################################################

DEBUG = True

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

SECRET_KEY = "django-insecure-+3tty1@(pff3fc^dn259a+ms6a#_(5f#@ss#h6s%21)qhh1x&0"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

#######################################################################################

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = ["http://localhost"]

# Application definition

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_htmx",
    "django_extensions",
    "widget_tweaks",
    "django_browser_reload",
    "debug_toolbar",
    "hyperpony",
    "main",
    "demo_address_book",
]

AUTH_USER_MODEL = "main.AppUser"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "hyperpony.middleware.HyperponyMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "project.wsgi.application"

# Database
SQLITE_DB_PATH = DATA_DIR / "sqlite" / "db.sqlite3"
SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(SQLITE_DB_PATH),
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {"timeout": 10},  # secs
    }
}

if "test" in sys.argv:
    TEMPLATE_DEBUG = False

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS: list = []

# Django allauth
# https://django-allauth.readthedocs.io/en/latest/configuration.html
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Mail Server
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS: list[str] = [
    # os.path.join(BASE_DIR, "..", "web", "build"),
]

STATIC_ROOT_DIR = DATA_DIR / "build" / "static"
STATIC_ROOT_DIR.mkdir(parents=True, exist_ok=True)
STATIC_ROOT = str(STATIC_ROOT_DIR)

# Uploaded media
MEDIA_URL = "media/"
MEDIA_ROOT = DATA_DIR / "media_root" / "uploaded"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {},
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {thread:d} {pathname}:{lineno} {message}",
            # "format": "{asctime} {levelname} {thread:d} {pathname}:{lineno} {message}",
            # 'format': '{levelname} {asctime} {module}: {message}',
            # 'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            "style": "{",
        },
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "htmxviews": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"),
            "propagate": False,
        },
        "main": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"),
            "propagate": False,
        },
        "project": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"),
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "WARN"),
            "propagate": False,
        },
    },
}
INTERNAL_IPS = ["127.0.0.1"]
