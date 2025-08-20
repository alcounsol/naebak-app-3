# نائبك دوت كوم - المشروع المعاد هيكلته

## نظرة عامة

هذا هو المشروع المعاد هيكلته لموقع "نائبك دوت كوم" باستخدام معايير Django الاحترافية مع فصل الصلاحيات بشكل صحيح. تم تصميم المشروع ليكون قابلاً للصيانة والتوسع والنشر على Google Cloud.

## الهيكل الجديد

```
naebak_project_root/
├── apps/                          # التطبيقات الفرعية
│   ├── core/                      # التطبيق الأساسي
│   ├── accounts/                  # إدارة المواطنين والحسابات
│   ├── candidates/                # إدارة المرشحين
│   ├── news/                      # إدارة الأخبار
│   ├── voting/                    # إدارة التصويت والتقييمات
│   └── messaging/                 # إدارة الرسائل
├── config/                        # إعدادات المشروع
│   ├── settings/                  # إعدادات البيئات المختلفة
│   │   ├── base.py               # الإعدادات الأساسية
│   │   ├── dev.py                # إعدادات التطوير
│   │   ├── prod.py               # إعدادات الإنتاج
│   │   └── test.py               # إعدادات الاختبار
│   ├── urls.py                   # URLs الرئيسية
│   ├── wsgi.py                   # WSGI للإنتاج
│   └── asgi.py                   # ASGI للـ WebSockets
├── templates/                     # القوالب منظمة حسب التطبيق
├── static/                        # الملفات الثابتة
├── requirements/                  # متطلبات البيئات المختلفة
├── scripts/                       # سكريبتات الإدارة
├── docker/                        # ملفات Docker
├── tests/                         # الاختبارات
└── manage.py                      # أداة إدارة Django
```

## المميزات الجديدة

### 1. فصل الصلاحيات
- **apps.core**: النماذج المشتركة والوظائف الأساسية
- **apps.accounts**: إدارة المواطنين والمصادقة
- **apps.candidates**: إدارة المرشحين والوعود الانتخابية
- **apps.news**: إدارة الأخبار والمحتوى
- **apps.voting**: إدارة التصويت والتقييمات
- **apps.messaging**: إدارة الرسائل والمحادثات

### 2. إعدادات البيئات المختلفة
- **dev.py**: بيئة التطوير مع SQLite وإعدادات مرنة
- **prod.py**: بيئة الإنتاج مع PostgreSQL و Redis
- **test.py**: بيئة الاختبار محسنة للسرعة

### 3. دعم النشر السحابي
- إعدادات Google Cloud Storage للملفات الثابتة
- دعم PostgreSQL و Redis
- ملفات Docker للحاويات
- سكريبتات النشر التلقائي

## التثبيت والتشغيل

### 1. متطلبات النظام
```bash
Python 3.11+
PostgreSQL 13+ (للإنتاج)
Redis 6+ (للإنتاج)
```

### 2. التثبيت المحلي
```bash
# استنساخ المشروع
cd naebak_project_root

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate     # Windows

# تثبيت المتطلبات
pip install -r requirements/dev.txt

# إعداد متغيرات البيئة
cp .env.example .env
# قم بتحرير .env وإضافة القيم المطلوبة

# تشغيل الهجرات
python manage.py migrate

# إنشاء مستخدم إداري
python manage.py createsuperuser

# تحميل البيانات التجريبية (اختياري)
python scripts/load_demo_data.py

# تشغيل الخادم
python manage.py runserver
```

### 3. التشغيل باستخدام Docker
```bash
# بناء وتشغيل الحاويات
cd docker
docker-compose up -d

# تشغيل الهجرات
docker-compose exec web python manage.py migrate

# إنشاء مستخدم إداري
docker-compose exec web python manage.py createsuperuser
```

## النشر على Google Cloud

### 1. إعداد Google Cloud
```bash
# تثبيت Google Cloud SDK
# إنشاء مشروع جديد
gcloud projects create naebak-project

# تفعيل الخدمات المطلوبة
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable redis.googleapis.com
```

### 2. إعداد قاعدة البيانات
```bash
# إنشاء قاعدة بيانات PostgreSQL
gcloud sql instances create naebak-db \
    --database-version=POSTGRES_13 \
    --tier=db-f1-micro \
    --region=us-central1

# إنشاء قاعدة البيانات
gcloud sql databases create naebak_db --instance=naebak-db

# إنشاء مستخدم
gcloud sql users create naebak_user \
    --instance=naebak-db \
    --password=your-secure-password
```

### 3. إعداد Redis
```bash
# إنشاء Redis instance
gcloud redis instances create naebak-redis \
    --size=1 \
    --region=us-central1
```

### 4. النشر
```bash
# بناء ونشر التطبيق
gcloud run deploy naebak \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

## الاختبار

### تشغيل الاختبارات
```bash
# تشغيل جميع الاختبارات
python manage.py test

# تشغيل اختبارات تطبيق معين
python manage.py test apps.candidates

# تشغيل مع تقرير التغطية
coverage run --source='.' manage.py test
coverage report
```

## الصيانة

### النسخ الاحتياطي
```bash
# إنشاء نسخة احتياطية
./scripts/backup.sh

# استعادة من نسخة احتياطية
python manage.py loaddata backup_file.json
```

### المراقبة
- استخدم Sentry للمراقبة والتتبع
- مراقبة الأداء عبر Google Cloud Monitoring
- سجلات التطبيق متاحة في Google Cloud Logging

## الأمان

### الإعدادات الأمنية
- HTTPS إجباري في الإنتاج
- CSRF protection مفعل
- XSS protection مفعل
- Content Security Policy مطبق
- Rate limiting على APIs

### أفضل الممارسات
- استخدم متغيرات البيئة للمعلومات الحساسة
- قم بتحديث المتطلبات بانتظام
- راجع سجلات الأمان دورياً

## المساهمة

### إرشادات التطوير
1. اتبع معايير PEP 8 للكود
2. اكتب اختبارات للميزات الجديدة
3. استخدم git flow للتطوير
4. وثق التغييرات في CHANGELOG

### هيكل الكود
- استخدم Class-based views عند الإمكان
- اتبع مبدأ DRY (Don't Repeat Yourself)
- اكتب docstrings للوظائف والكلاسات
- استخدم type hints في Python

## الدعم

للحصول على الدعم أو الإبلاغ عن مشاكل:
- راجع الوثائق أولاً
- تحقق من السجلات للأخطاء
- أنشئ issue في نظام إدارة المشروع

## الترخيص

هذا المشروع مرخص تحت رخصة MIT. راجع ملف LICENSE للتفاصيل.

---

## ملاحظات التطوير

### التغييرات الرئيسية في إعادة الهيكلة:

1. **تقسيم التطبيقات**: تم تقسيم التطبيق الواحد إلى 6 تطبيقات منفصلة
2. **إعدادات البيئات**: تم إنشاء إعدادات منفصلة لكل بيئة
3. **تحسين الأداء**: إضافة Redis للتخزين المؤقت
4. **الأمان**: تطبيق أفضل ممارسات الأمان
5. **النشر**: دعم كامل للنشر السحابي

### المشاكل المحلولة:
- فصل الاهتمامات بشكل صحيح
- تحسين قابلية الصيانة
- دعم التوسع الأفقي
- تحسين الأداء والأمان

### التحسينات المستقبلية:
- إضافة API REST كامل
- تطبيق WebSockets للرسائل الفورية
- تحسين واجهة المستخدم
- إضافة المزيد من الاختبارات

