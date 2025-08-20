"""
إعدادات بيئة الاختبار لمشروع نائبك دوت كوم
"""

from .base import *

# Debug mode for testing
DEBUG = True

# Test database (in-memory SQLite for speed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Cache configuration for testing (dummy cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Password hashers for testing (faster)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Static files for testing
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files for testing
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Session configuration for testing
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Channels configuration for testing
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Logging configuration for testing (minimal)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'CRITICAL',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'CRITICAL',
    },
}

# Security settings for testing (relaxed)
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# CORS settings for testing
CORS_ALLOW_ALL_ORIGINS = True

# Test-specific settings
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
TESTING = True

# Disable unnecessary middleware for testing
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# Remove unnecessary apps for testing
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in [
    'debug_toolbar',
    'compressor',
]]

