"""
تكوين تطبيق core
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    تكوين تطبيق core الرئيسي
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'نائبك دوت كوم - الأساسيات'
    
    def ready(self):
        """
        يتم تنفيذ هذه الدالة عند تحميل التطبيق
        """
        # استيراد الإشارات (signals) إذا كانت موجودة
        try:
            import apps.core.signals
        except ImportError:
            pass
