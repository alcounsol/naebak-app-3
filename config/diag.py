# config/diag.py
import os, socket, json
from django.conf import settings
from django.db import connections
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET

def _mask(value, keep=2):
    if not value:
        return value
    s = str(value)
    if len(s) <= keep:
        return "*" * len(s)
    return "*" * (len(s) - keep) + s[-keep:]

@require_GET
def env_check(request):
    # حماية بسيطة بتوكن
    expected = os.environ.get("DIAG_TOKEN")
    if not expected or request.headers.get("X-Diag-Token") != expected:
        return HttpResponseForbidden("Forbidden")

    # اجمع المتغيرات من البيئة
    env = {
        "DJANGO_SETTINGS_MODULE": os.environ.get("DJANGO_SETTINGS_MODULE"),
        "DEBUG": os.environ.get("DEBUG"),
        "ALLOWED_HOSTS_env": os.environ.get("ALLOWED_HOSTS"),
        "DB_HOST": os.environ.get("DB_HOST"),
        "DB_PORT": os.environ.get("DB_PORT"),
        "DB_NAME": os.environ.get("DB_NAME"),
        "DB_USER": os.environ.get("DB_USER"),
        "REDIS_URL": os.environ.get("REDIS_URL"),
        "REDIS_HOST": os.environ.get("REDIS_HOST"),
        "REDIS_PORT": os.environ.get("REDIS_PORT"),
        "CSRF_TRUSTED_ORIGINS": os.environ.get("CSRF_TRUSTED_ORIGINS"),
        "INSTANCE_CONNECTION_NAME": os.environ.get("INSTANCE_CONNECTION_NAME"),
    }

    # اجمع القيم الفعلية داخل Django settings
    dj = {
        "DEBUG": getattr(settings, "DEBUG", None),
        "ALLOWED_HOSTS": getattr(settings, "ALLOWED_HOSTS", None),
        "CSRF_TRUSTED_ORIGINS": getattr(settings, "CSRF_TRUSTED_ORIGINS", None),
        "DATABASES_DEFAULT": {
            "ENGINE": settings.DATABASES["default"]["ENGINE"],
            "NAME": settings.DATABASES["default"]["NAME"],
            "USER": settings.DATABASES["default"]["USER"],
            "HOST": settings.DATABASES["default"]["HOST"],
            "PORT": settings.DATABASES["default"]["PORT"],
        },
        "CACHES_DEFAULT": getattr(settings, "CACHES", {}).get("default"),
    }

    # شيّك اتصال Postgres
    db_ok = False
    db_info = {}
    try:
        with connections["default"].cursor() as cur:
            cur.execute("SELECT current_user, current_database(), inet_server_addr(), version();")
            row = cur.fetchone()
            db_ok = True
            db_info = {
                "current_user": row[0],
                "current_database": row[1],
                "server_addr": str(row[2]),
                "version": row[3][:60] + "..." if row[3] else None,
            }
    except Exception as e:
        db_info = {"error": str(e)}

    # شيّك اتصال Redis
    redis_ok = False
    redis_info = {}
    try:
        import redis
        url = os.environ.get("REDIS_URL")
        if not url:
            host = os.environ.get("REDIS_HOST", "localhost")
            port = int(os.environ.get("REDIS_PORT", "6379"))
            url = f"redis://{host}:{port}/0"
        r = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        pong = r.ping()
        redis_ok = bool(pong)
        redis_info = {"url_used": url, "ping": pong}
    except Exception as e:
        redis_info = {"error": str(e)}

    # أخفي الباسوردات
    secrets = {
        "DB_PASSWORD_present": bool(os.environ.get("DB_PASSWORD")),
        "DB_PASSWORD_masked": _mask(os.environ.get("DB_PASSWORD") or ""),
        "SECRET_KEY_present": bool(os.environ.get("SECRET_KEY")),
        "SECRET_KEY_masked": _mask(os.environ.get("SECRET_KEY") or ""),
    }

    return JsonResponse({
        "hostname": socket.gethostname(),
        "env": env,
        "django": dj,
        "db": {"ok": db_ok, "info": db_info},
        "redis": {"ok": redis_ok, "info": redis_info},
        "secrets": secrets,
    })
