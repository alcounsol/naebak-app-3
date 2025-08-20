
"""
إعدادات Django لبيئة الإنتاج - نسخة نظيفة ومهيأة للعمل على Google Cloud Run
"""
from .base import *
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

STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'naebak-static-media'
GS_PROJECT_ID = 'stalwart-star-468902-j1'
GS_AUTO_CREATE_BUCKET = False
GS_DEFAULT_ACL = 'publicRead'
STATIC_URL = 'https://storage.googleapis.com/naebak-static-media/static/'
MEDIA_URL = 'https://storage.googleapis.com/naebak-static-media/media/'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "jklgfdgDRGDGDweasdgds344$^$%^%$^$%^%$^%FSFFSH",
        "USER": "hasdhflsgFDG%^%^ADSGDG$$#5654645$642%6SHFHS",
        "PASSWORD": "D249328C34F63A1EA1DAEB844D8AF",
        "HOST": "/cloudsql/naebak-app:europe-west1:naebak-db",
        "PORT": "5432",
        "OPTIONS": {"sslmode": "disable"},
    }
}

REDIS_HOST = "10.190.151.116"
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARTS": {"ssl_cert_reqs": None},
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
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"],"level": "INFO","propagate": False},
        "naebak": {"handlers": ["console"],"level": "INFO","propagate": False},
    },
}




