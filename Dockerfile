# === Base Image ===
FROM python:3.11-slim

# === System deps ===
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# === Env ===
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    PORT=8080

# === Workdir ===
WORKDIR /app

# === Python deps ===
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# === App code ===
COPY . /app

# === Folders ===
RUN mkdir -p /app/staticfiles /app/media /app/logs

# === أهم نقطة: نجبر التجميع المحلي بعيداً عن GCS أثناء الـ build ===
ENV STATIC_BACKEND=local

# === Collect static ===
RUN python manage.py collectstatic --noinput --settings=config.settings.prod

# === Expose & Run ===
EXPOSE 8080
# استخدم نفس الـ WSGI السابق عندك (غيّره فقط لو مشروعك ASGI وتستعمل daphne/uvicorn)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "8", "--timeout", "0"]
