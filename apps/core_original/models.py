from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Candidate(models.Model):
    """Model representing a candidate"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    name = models.CharField(max_length=200, verbose_name="اسم المرشح")
    role = models.CharField(max_length=200, default="مرشح مجلس النواب", verbose_name="المنصب")
    
    # Use governorate_id instead of ForeignKey to JSON data
    governorate_id = models.PositiveIntegerField(verbose_name="المحافظة", help_text="معرف المحافظة من ملف JSON")
    constituency = models.CharField(max_length=200, verbose_name="الدائرة الانتخابية")
    profile_picture = models.ImageField(upload_to='candidate_profiles/', null=True, blank=True, verbose_name="الصورة الشخصية")
    banner_image = models.ImageField(upload_to='candidate_banners/', null=True, blank=True, verbose_name="صورة البانر")
    bio = models.TextField(verbose_name="البيان الشخصي", blank=True)
    
    # Enhanced candidate profile fields
    electoral_program = models.TextField(verbose_name="البرنامج الانتخابي", blank=True, help_text="البرنامج الانتخابي المفصل للمرشح")
    message_to_voters = models.TextField(verbose_name="كلمة للمنتخبين", blank=True, help_text="كلمة موجزة من المرشح لمنتخبيه")
    youtube_video_url = models.URLField(verbose_name="رابط فيديو يوتيوب", blank=True, help_text="رابط فيديو تعريفي أو برنامج انتخابي على يوتيوب")
    facebook_url = models.URLField(verbose_name="رابط فيسبوك", blank=True)
    twitter_url = models.URLField(verbose_name="رابط تويتر", blank=True)
    website_url = models.URLField(verbose_name="الموقع الشخصي", blank=True)
    phone_number = models.CharField(max_length=20, verbose_name="رقم الهاتف", blank=True)
    
    is_featured = models.BooleanField(default=False, verbose_name="مرشح مميز في المحافظة")
    election_symbol = models.CharField(max_length=50, blank=True, verbose_name="رمز الترشح")
    election_number = models.CharField(max_length=50, blank=True, verbose_name="الرقم الانتخابي")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مرشح"
        verbose_name_plural = "المرشحون"

    def __str__(self):
        return self.name
    
    @property
    def governorate_name(self):
        """Get governorate name from JSON data"""
        from .utils import get_governorate_by_id
        gov_data = get_governorate_by_id(self.governorate_id)
        return gov_data['name_ar'] if gov_data else "غير محدد"
    
    @property
    def governorate_data(self):
        """Get full governorate data from JSON"""
        from .utils import get_governorate_by_id
        return get_governorate_by_id(self.governorate_id)


class ElectoralPromise(models.Model):
    """Model representing electoral promises"""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='electoral_promises')
    title = models.CharField(max_length=300, verbose_name="عنوان الوعد")
    description = models.TextField(verbose_name="وصف الوعد")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "وعد انتخابي"
        verbose_name_plural = "الوعود الانتخابية"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.candidate.name} - {self.title}"


class PublicServiceHistory(models.Model):
    """Model representing public service history"""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='service_history')
    start_year = models.PositiveIntegerField(verbose_name="سنة البداية")
    end_year = models.PositiveIntegerField(verbose_name="سنة النهاية")
    position = models.CharField(max_length=300, verbose_name="المنصب")
    description = models.TextField(verbose_name="وصف الإنجازات والمسؤوليات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تاريخ في العمل العام"
        verbose_name_plural = "التاريخ في العمل العام"
        ordering = ['-start_year']

    def __str__(self):
        return f"{self.candidate.name} - {self.position} ({self.start_year}-{self.end_year})"


class Message(models.Model):
    """Model representing messages from citizens to candidates"""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='messages')
    sender_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المرسل المسجل")
    sender_name = models.CharField(max_length=200, verbose_name="اسم المرسل", blank=True)
    sender_email = models.EmailField(verbose_name="بريد المرسل", blank=True)
    subject = models.CharField(max_length=300, verbose_name="موضوع الرسالة")
    content = models.TextField(verbose_name="محتوى الرسالة")
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True, verbose_name="مرفق")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت الإرسال")
    is_read = models.BooleanField(default=False, verbose_name="مقروءة")
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        verbose_name = "رسالة"
        verbose_name_plural = "الرسائل"
        ordering = ['-timestamp']

    def __str__(self):
        sender = self.sender_user.get_full_name() if self.sender_user else self.sender_name
        return f"رسالة من {sender} إلى {self.candidate.name}"


class Rating(models.Model):
    """Model representing ratings and comments from citizens"""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ratings')
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المواطن")
    stars = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="التقييم بالنجوم")
    comment = models.TextField(verbose_name="التعليق", blank=True)
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت التقييم")
    is_read = models.BooleanField(default=False, verbose_name="مقروء")

    class Meta:
        verbose_name = "تقييم"
        verbose_name_plural = "التقييمات"
        ordering = ['-timestamp']
        unique_together = ['candidate', 'citizen']  # One rating per citizen per candidate

    def __str__(self):
        return f"تقييم {self.stars} نجوم من {self.citizen.get_full_name()} للمرشح {self.candidate.name}"


class RatingReply(models.Model):
    """Model representing replies to ratings from candidates"""
    rating = models.OneToOneField(Rating, on_delete=models.CASCADE, related_name='reply')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="رد المرشح")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت الرد")

    class Meta:
        verbose_name = "رد على تقييم"
        verbose_name_plural = "الردود على التقييمات"

    def __str__ (self):
        return f"رد {self.candidate.name} على تقييم {self.rating.citizen.get_full_name()}"


class Vote(models.Model):
    """Model representing votes (approve/disapprove) for candidates"""
    VOTE_CHOICES = [
        ('approve', 'أؤيد'),
        ('disapprove', 'أعارض'),
    ]
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المواطن")
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES, verbose_name="نوع التصويت")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت التصويت")

    class Meta:
        verbose_name = "تصويت"
        verbose_name_plural = "التصويتات"
        ordering = ['-timestamp']
        unique_together = ['candidate', 'citizen']  # One vote per citizen per candidate

    def __str__(self):
        return f"{self.get_vote_type_display()} من {self.citizen.get_full_name()} للمرشح {self.candidate.name}"


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



class Citizen(models.Model):
    """Model representing a citizen"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="citizen_profile")
    first_name = models.CharField(max_length=100, verbose_name="الاسم الأول")
    last_name = models.CharField(max_length=100, verbose_name="الاسم الأخير")
    email = models.EmailField(unique=True, verbose_name="البريد الإلكتروني")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    governorate = models.ForeignKey("Governorate", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المحافظة")
    area_type = models.CharField(max_length=50, blank=True, verbose_name="نوع المنطقة")
    area_name = models.CharField(max_length=200, blank=True, verbose_name="اسم المنطقة")
    address = models.TextField(blank=True, verbose_name="عنوان المراسلات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مواطن"
        verbose_name_plural = "المواطنون"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Governorate(models.Model):
    """Model representing a governorate"""
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم المحافظة")
    # Add any other fields relevant to a governorate, e.g., population, area, etc.

    class Meta:
        verbose_name = "محافظة"
        verbose_name_plural = "المحافظات"

    def __str__(self):
        return self.name





class FeaturedCandidate(models.Model):
    """Model to mark candidates as featured"""
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name='featured_candidate')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مرشح مميز"
        verbose_name_plural = "المرشحون المميزون"

    def __str__(self):
        return f"المرشح المميز: {self.candidate.name}"

