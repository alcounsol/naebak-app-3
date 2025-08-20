إعداد بيئة Cloud Run:
- اضبط متغيرات البيئة على الخدمة: SECRET_KEY, DEBUG=False, ALLOWED_HOSTS
- قاعدة البيانات (اختياري): Cloud SQL Postgres + add-cloudsql-instances + DB_* (واستخدم DB_HOST=/cloudsql/PROJECT:REGION:INSTANCE)
- لملفات media يُفضَّل Google Cloud Storage مع django-storages
