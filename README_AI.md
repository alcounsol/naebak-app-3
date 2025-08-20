# معلومات مشروع Naebak (خاص بالذكاء الاصطناعي)

هذا الملف يحتوي على معلومات مفصلة حول مشروع Naebak، وهو مخصص للاستخدام من قبل نماذج الذكاء الاصطناعي لمساعدتي في التطوير والنشر. يرجى عدم مشاركة هذا الملف علنًا أو على منصات مثل GitHub.

## 1. نظرة عامة على المشروع

Naebak هو تطبيق ويب مبني باستخدام إطار عمل Django (Python) ويستخدم PostgreSQL كقاعدة بيانات و Redis للتخزين المؤقت وقنوات الاتصال. تم تصميم التطبيق للنشر على Google Cloud Run، مع استخدام Google Cloud Storage للملفات الثابتة والوسائط.

## 2. بيانات الاعتماد والاتصال (Google Cloud - naebak-app)

تم تكوين المشروع للعمل مع مشروع Google Cloud `naebak-app` في منطقة `europe-west1`.

### 2.1. قاعدة البيانات (PostgreSQL - Cloud SQL)

*   **اسم Instance:** `naebak-db`
*   **Connection Name:** `naebak-app:europe-west1:naebak-db`
*   **اسم قاعدة البيانات:** `jklgfdgDRGDGDweasdgds344$^$%^%$^$%^%$^%FSFFSH`
*   **اسم المستخدم:** `hasdhflsgFDG%^%^ADSGDG$$#5654645$642%6SHFHS`
*   **كلمة المرور:** `D249328C34F63A1EA1DAEB844D8AF`

### 2.2. التخزين المؤقت (Redis - Memorystore)

*   **اسم Instance:** `naebak-redis`
*   **عنوان IP للمضيف (Host IP):** `10.190.151.116`

### 2.3. التخزين السحابي (Google Cloud Storage)

*   **اسم Bucket:** `naebak-static-media`
*   **مسار الملفات الثابتة (STATIC_URL):** `https://storage.googleapis.com/naebak-static-media/static/`
*   **مسار ملفات الوسائط (MEDIA_URL):** `https://storage.googleapis.com/naebak-static-media/media/`

### 2.4. مفتاح Django السري (SECRET_KEY)

*   **القيمة:** `ffd;gjsfd556546$$^$^VBNgfngFY^^U^##@#$2FFHsfh`

## 3. هيكلة المشروع بعد التعديل

تم تعديل هيكلة المشروع لتبسيط عملية النشر وجعلها أكثر وضوحًا. تم نقل الملفات الأساسية الخاصة بالـ Docker والاحتياجات إلى جذر المشروع.

*   `Dockerfile`: ملف بناء صورة Docker للتطبيق.
*   `docker-compose.yml`: ملف لتشغيل التطبيق محليًا باستخدام Docker Compose.
*   `nginx.conf`: إعدادات Nginx (إذا كان يستخدم كـ reverse proxy).
*   `requirements.txt`: قائمة بجميع تبعيات Python المطلوبة للمشروع.

تم حذف المجلدات القديمة `docker/` و `requirements/`.

## 4. تبعيات Python (requirements.txt)

يحتوي ملف `requirements.txt` الآن على جميع التبعيات اللازمة لتشغيل التطبيق. تم التأكد من إضافة `google-cloud-storage`.

```
Django==5.0.6
djangorestframework==3.15.1
psycopg2-binary==2.9.9
redis==5.0.4
django-redis==5.4.0
channels==4.0.0
channels-redis==4.2.0
celery==5.3.6
gunicorn==21.2.0
django-cors-headers==4.3.1
django-ratelimit==4.1.0
Pillow==10.3.0
python-decouple==3.8
whitenoise==6.6.0
django-crispy-forms==2.1
crispy-bootstrap5==2024.2
django-modeltranslation==0.18.11
django-admin-interface==0.28.6
django-colorfield==0.11.0
django-storages==1.14.2
python-slugify==8.0.4
google-cloud-storage==2.11.0
```

## 5. ملاحظات للنشر والتطوير المستقبلي

*   **Cloud Run:** عند النشر على Cloud Run، تأكد من ربط خدمة Cloud Run بـ Cloud SQL Instance (`naebak-db`) واستخدام متغيرات البيئة المناسبة للاتصال بـ Redis.
*   **متغيرات البيئة:** يفضل استخدام Secret Manager في Google Cloud لتخزين البيانات الحساسة مثل كلمات المرور ومفتاح Django السري، وربطها بـ Cloud Run كمتغيرات بيئة.
*   **التطوير المحلي:** يمكن استخدام `docker-compose.yml` لتشغيل بيئة تطوير محلية مطابقة لبيئة الإنتاج.
*   **تغيير حساب Google Cloud:** في حال تغيير حساب Google Cloud أو المشروع، يجب تحديث جميع بيانات الاعتماد المذكورة أعلاه في ملفات إعدادات التطبيق (خاصة `config/settings/prod.py`) وفي هذا الملف `README_AI.md`.

هذا الملف هو مرجع شامل لأي نموذج ذكاء اصطناعي يحتاج إلى فهم عميق لإعدادات المشروع وهيكلته لمساعدتك في أي مهام مستقبلية تتعلق بالتطوير أو النشر.

