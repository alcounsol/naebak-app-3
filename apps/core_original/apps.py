"""
تكوين تطبيق naebak
"""

from django.apps import AppConfig


class NaebakConfig(AppConfig):
    """
    تكوين تطبيق naebak الرئيسي
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'naebak'
    verbose_name = 'نائبك دوت كوم'
    
    def ready(self):
        """
        يتم تنفيذ هذه الدالة عند تحميل التطبيق
        """
        # استيراد الإشارات (signals) إذا كانت موجودة
        try:
            import naebak.signals
        except ImportError:
            pass
