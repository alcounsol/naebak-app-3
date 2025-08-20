from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class News(models.Model):
    """Model for managing news ticker content"""
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('published', 'منشور'),
        ('archived', 'مؤرشف'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('normal', 'عادية'),
        ('high', 'عالية'),
        ('urgent', 'عاجل'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="عنوان الخبر")
    content = models.TextField(verbose_name="محتوى الخبر")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="حالة الخبر")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name="أولوية الخبر")
    
    # Display settings
    show_on_homepage = models.BooleanField(default=True, verbose_name="عرض في الصفحة الرئيسية")
    show_on_ticker = models.BooleanField(default=True, verbose_name="عرض في الشريط الإخباري")
    ticker_speed = models.PositiveIntegerField(default=50, verbose_name="سرعة التمرير (بالثانية)")
    
    # Scheduling
    publish_date = models.DateTimeField(default=timezone.now, verbose_name="تاريخ النشر")
    expire_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ انتهاء الصلاحية")
    
    # Metadata
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="الكاتب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    views_count = models.PositiveIntegerField(default=0, verbose_name="عدد المشاهدات")
    
    # SEO and social media
    meta_description = models.CharField(max_length=160, blank=True, verbose_name="وصف ميتا")
    tags = models.CharField(max_length=200, blank=True, verbose_name="الكلمات المفتاحية")
    
    class Meta:
        verbose_name = "خبر"
        verbose_name_plural = "الأخبار"
        ordering = ['-priority', '-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['status', 'publish_date']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def is_published(self):
        """Check if news is currently published and not expired"""
        now = timezone.now()
        return (
            self.status == 'published' and
            self.publish_date <= now and
            (self.expire_date is None or self.expire_date > now)
        )
    
    def get_priority_class(self):
        """Get CSS class for priority styling"""
        priority_classes = {
            'low': 'priority-low',
            'normal': 'priority-normal',
            'high': 'priority-high',
            'urgent': 'priority-urgent'
        }
        return priority_classes.get(self.priority, 'priority-normal')
    
    def increment_views(self):
        """Increment views count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    @classmethod
    def get_active_news(cls):
        """Get all currently active news"""
        now = timezone.now()
        return cls.objects.filter(
            status='published',
            publish_date__lte=now
        ).filter(
            models.Q(expire_date__isnull=True) | models.Q(expire_date__gt=now)
        )
    
    @classmethod
    def get_ticker_news(cls):
        """Get news for ticker display"""
        return cls.get_active_news().filter(show_on_ticker=True)
    
    @classmethod
    def get_homepage_news(cls):
        """Get news for homepage display"""
        return cls.get_active_news().filter(show_on_homepage=True)
