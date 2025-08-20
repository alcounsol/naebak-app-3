from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Governorate(models.Model):
    """Model representing a governorate"""
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم المحافظة")
    # Add any other fields relevant to a governorate, e.g., population, area, etc.

    class Meta:
        verbose_name = "محافظة"
        verbose_name_plural = "المحافظات"

    def __str__(self):
        return self.name


class ActivityLog(models.Model):
    """Model for logging user activities and system events"""
    ACTION_TYPES = [
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('register', 'تسجيل حساب جديد'),
        ('profile_update', 'تحديث الملف الشخصي'),
        ('message_sent', 'إرسال رسالة'),
        ('message_reply', 'الرد على رسالة'),
        ('rating_given', 'إعطاء تقييم'),
        ('vote_cast', 'إدلاء بصوت'),
        ('promise_created', 'إنشاء وعد انتخابي'),
        ('promise_updated', 'تحديث وعد انتخابي'),
        ('promise_deleted', 'حذف وعد انتخابي'),
        ('news_created', 'إنشاء خبر'),
        ('news_updated', 'تحديث خبر'),
        ('news_deleted', 'حذف خبر'),
        ('news_published', 'نشر خبر'),
        ('candidate_created', 'إنشاء حساب مرشح'),
        ('candidate_updated', 'تحديث بيانات مرشح'),
        ('candidate_deleted', 'حذف حساب مرشح'),
        ('user_created', 'إنشاء حساب مستخدم'),
        ('user_updated', 'تحديث بيانات مستخدم'),
        ('user_deleted', 'حذف حساب مستخدم'),
        ('backup_created', 'إنشاء نسخة احتياطية'),
        ('backup_restored', 'استعادة نسخة احتياطية'),
        ('system_error', 'خطأ في النظام'),
        ('security_alert', 'تنبيه أمني'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'معلومات'),
        ('warning', 'تحذير'),
        ('error', 'خطأ'),
        ('critical', 'حرج'),
    ]
    
    # Basic information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المستخدم")
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES, verbose_name="نوع النشاط")
    description = models.TextField(verbose_name="وصف النشاط")
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info', verbose_name="مستوى الأهمية")
    
    # Context information
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="معلومات المتصفح")
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name="مفتاح الجلسة")
    
    # Related objects (generic foreign key for flexibility)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional data (JSON field for extra information)
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="بيانات إضافية")
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت النشاط")
    
    class Meta:
        verbose_name = "سجل نشاط"
        verbose_name_plural = "سجلات الأنشطة"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        user_name = self.user.get_full_name() if self.user else "مجهول"
        return f"{user_name} - {self.get_action_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def get_severity_class(self):
        """Get CSS class for severity styling"""
        severity_classes = {
            'info': 'severity-info',
            'warning': 'severity-warning', 
            'error': 'severity-error',
            'critical': 'severity-critical'
        }
        return severity_classes.get(self.severity, 'severity-info')
    
    def get_severity_icon(self):
        """Get FontAwesome icon for severity"""
        severity_icons = {
            'info': 'fas fa-info-circle',
            'warning': 'fas fa-exclamation-triangle',
            'error': 'fas fa-times-circle',
            'critical': 'fas fa-skull-crossbones'
        }
        return severity_icons.get(self.severity, 'fas fa-info-circle')
    
    @classmethod
    def log_activity(cls, user, action_type, description, severity='info', ip_address=None, user_agent=None, session_key=None, content_object=None, extra_data=None):
        """Helper method to create activity log entries"""
        return cls.objects.create(
            user=user,
            action_type=action_type,
            description=description,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key,
            content_object=content_object,
            extra_data=extra_data or {}
        )
    
    @classmethod
    def get_recent_activities(cls, limit=50):
        """Get recent activities"""
        return cls.objects.select_related('user').order_by('-timestamp')[:limit]
    
    @classmethod
    def get_user_activities(cls, user, limit=50):
        """Get activities for a specific user"""
        return cls.objects.filter(user=user).order_by('-timestamp')[:limit]
    
    @classmethod
    def get_security_alerts(cls, limit=20):
        """Get recent security-related activities"""
        security_actions = ['login', 'logout', 'register', 'security_alert']
        return cls.objects.filter(
            action_type__in=security_actions
        ).order_by('-timestamp')[:limit]
    
    @classmethod
    def get_critical_activities(cls, limit=20):
        """Get critical activities"""
        return cls.objects.filter(
            severity__in=['error', 'critical']
        ).order_by('-timestamp')[:limit]

