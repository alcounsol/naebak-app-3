from django.db import models
from django.contrib.auth.models import User
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
        from apps.core.utils import get_governorate_by_id
        gov_data = get_governorate_by_id(self.governorate_id)
        return gov_data['name_ar'] if gov_data else "غير محدد"
    
    @property
    def governorate_data(self):
        """Get full governorate data from JSON"""
        from apps.core.utils import get_governorate_by_id
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


class FeaturedCandidate(models.Model):
    """Model to mark candidates as featured"""
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name='featured_candidate')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مرشح مميز"
        verbose_name_plural = "المرشحون المميزون"

    def __str__(self):
        return f"المرشح المميز: {self.candidate.name}"
