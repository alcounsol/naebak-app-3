FROM python:3.11-slim

# تثبيت المتطلبات النظام
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    PORT=8080

# إنشاء مجلد العمل
WORKDIR /app

# نسخ وتثبيت المتطلبات أولاً (للاستفادة من cache)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# نسخ المشروع
COPY . /app

# إنشاء المجلدات المطلوبة
RUN mkdir -p /app/staticfiles /app/media /app/logs

# تجميع الملفات الثابتة
RUN python manage.py collectstatic --noinput --settings=config.settings.prod

# إنشاء مستخدم غير root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# فتح المنفذ
EXPOSE 8080

# تشغيل التطبيق
CMD gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

