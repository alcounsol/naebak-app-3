# تقرير تحديث إعدادات تطبيق Naebak

تم تحديث ملف `config/settings/prod.py` في تطبيق Naebak بالبيانات الجديدة الخاصة بمشروع Google Cloud `naebak-app` في منطقة `europe-west1`.

## التغييرات التي تم إجراؤها:

1.  **مفتاح Django السري (`SECRET_KEY`):**
    *   تم تحديثه إلى القيمة الجديدة المقدمة: `ffd;gjsfd556546$$^$^VBNgfngFY^^U^##@#$2FFHsfh`.

2.  **اسم سلة التخزين السحابي (`GS_BUCKET_NAME`):**
    *   تم تحديثه من `naebak-static-media-files` إلى `naebak-static-media`.

3.  **مسار الملفات الثابتة (`STATIC_URL`):**
    *   تم تحديث المسار ليعكس اسم سلة التخزين الجديدة: `https://storage.googleapis.com/naebak-static-media/static/`.

4.  **مسار ملفات الوسائط (`MEDIA_URL`):**
    *   تم تحديث المسار ليعكس اسم سلة التخزين الجديدة: `https://storage.googleapis.com/naebak-static-media/media/`.

5.  **إعدادات قاعدة البيانات (`DATABASES`):**
    *   تم تحديث `NAME` و`USER` و`PASSWORD` بالقيم الجديدة المقدمة.
    *   تم تحديث `HOST` إلى `cloudsql/naebak-app:europe-west1:naebak-db`.
    *   تم تغيير `sslmode` إلى `disable` ليتوافق مع الاتصال عبر `cloudsql`.

6.  **إعدادات Redis Host (`REDIS_HOST`):**
    *   تم تحديثه إلى عنوان IP الجديد: `10.190.151.116`.


هذه التغييرات تضمن أن التطبيق سيستخدم بيانات الاعتماد الصحيحة والاتصالات المناسبة عند النشر على Google Cloud Run.

الخطوة التالية هي إعداد Cloud Build للنشر، أو يمكنك الآن بناء الصورة ونشرها يدويًا إذا كنت تفضل ذلك.

