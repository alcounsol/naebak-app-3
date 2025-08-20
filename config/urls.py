"""
تكوين URLs الرئيسي لمشروع نائبك دوت كوم
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # لوحة الإدارة
    path('admin/', admin.site.urls),
    
    # التطبيق الرئيسي
    path("", include("apps.core.urls")),
    
    # تطبيقات فرعية
    path("candidates/", include("apps.candidates.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("messages/", include("apps.messaging.urls")),
    path("news/", include("apps.news.urls")),
    path("voting/", include("apps.voting.urls")),
]

# إضافة URLs للملفات الثابتة والوسائط في بيئة التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # إضافة Debug Toolbar في بيئة التطوير
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns

# تخصيص عناوين لوحة الإدارة
admin.site.site_header = "إدارة موقع نائبك دوت كوم"
admin.site.site_title = "نائبك دوت كوم"
admin.site.index_title = "لوحة التحكم الرئيسية"
