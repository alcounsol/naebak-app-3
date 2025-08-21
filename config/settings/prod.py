"""
إعدادات Django لبيئة الإنتاج - مُهيأة للعمل على Cloud Run مع تبديل مرن
بين static المحلي (WhiteNoise) و Google Cloud Storage عبر متغير بيئة.
"""
from .base import *  # noqa
from decouple import config
import os

DEBUG = config("DEBUG", default=False, cast=bool)
SECRET_KEY = "ffd;gjsfd556546$$^$^VBNgfngFY^^U^##@#$2FFHsfh"
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)

_default_csrf = "https://*.run.app,https://*.a.run.app"
CSRF_TRUSTED_ORIGINS = [o for o in config("CSRF_TRUSTED_ORIGINS", default=_default_csrf).split(",") if o]

CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=True, cast=bool)
if not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = [o for o in config("CORS_ALLOWED_ORIGINS", default="").split(",") if o]
CORS_ALLOW_CREDENTIALS = True

# -------- Static/Media: تبديل مرن بين المحلي و GCS --------
# STATIC_BACKEND=local (افتراضي) يجمع ويقدم الستاتيك محلياً عبر WhiteNoise داخل الكونتينر.
# STATIC_BACKEND=gcs لتقديم/تخزين الملفات عبر Google Cloud Storage في وقت التشغيل.
STATIC_BACKEND = os.getenv("STATIC_BACKEND", "local").lower()

# مسارات محلية
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
# BASE_DIR جاي من base.py
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

# تأكد من إضافة WhiteNoise في الميدلوير (لو مش موجود)
_whitenoise = "whitenoise.middleware.WhiteNoiseMiddleware"
if _whitenoise not in MIDDLEWARE:
    try:
        sec_idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
        MIDDLEWARE.insert(sec_idx + 1, _whitenoise)
    except ValueError:
        # لو مش لاقي SecurityMiddleware نحط WhiteNoise في أول المصفوفة
        MIDDLEWARE = [_whitenoise] + list(MIDDLEWARE)

if STATIC_BACKEND == "local":
    # تقديم الستاتيك من داخل الكونتينر
    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "LOCATION": str(MEDIA_ROOT),
            "BASE_URL": MEDIA_URL,
        },
    }
    # تحسين الكاش للستاتيك
    WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365
else:
    # إعدادات GCS (لو حبيت ترجع لها وقت التشغيل)
    GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME", "naebak-static-media")
    GS_PROJECT_ID = os.getenv("GS_PROJECT_ID", "stalwart-star-468902-j1")
    GS_AUTO_CREATE_BUCKET = False
    GS_DEFAULT_ACL = "publicRead"

    STORAGES = {
        "staticfiles": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "GS_BUCKET_NAME": GS_BUCKET_NAME,
        },
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "GS_BUCKET_NAME": GS_BUCKET_NAME,
        },
    }

    # عند استخدام GCS يمكنك تغيير الروابط لو عايز روابط مطلقة
    STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"

# -------- قاعدة البيانات --------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "jklgfdgDRGDGDweasdgds344$^$%^%$^$%^%$^%FSFFSH",
        "USER": "hasdhflsgFDG%^%^ADSGDG$$#5654645$642%6SHFHS",
        "PASSWORD": "D249328C34F63A1EA1DAEB844D8AF",
        "HOST": "/cloudsql/naebak-app:europe-west1:naebak-db",  # Cloud SQL Socket
        "PORT": "5432",
        "OPTIONS": {"sslmode": "disable"},
    }
}

# -------- Redis / Cache / Channels --------
REDIS_HOST = "10.190.151.116"
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # تصحيح المفتاح (كان KWARTS)
            "CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": None},
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

# -------- أمان الكوكيز --------
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# -------- لوجينج --------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "naebak": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# إزالة debug_toolbar لو موجود
if "debug_toolbar" in INSTALLED_APPS:
    INSTALLED_APPS.remove("debug_toolbar")
if "debug_toolbar.middleware.DebugToolbarMiddleware" in MIDDLEWARE:
    MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")
