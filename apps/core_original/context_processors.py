"""
معالجات السياق (Context Processors) لتطبيق naebak
توفر متغيرات عامة لجميع القوالب
"""

from django.conf import settings

def site_context(request):
    """
    معالج السياق الرئيسي للموقع
    يوفر المتغيرات العامة المطلوبة في جميع القوالب
    """
    
    # إحصائيات الموقع (سيتم تطويرها لاحقاً)
    stats = {
        'total_governorates': 0,
        'total_candidates': 0,
        'total_voters': 0,
        'online_visitors': 0,
    }
    
    return {
        'site_name': 'نائبك دوت كوم',
        'site_description': 'حلقة الوصل بين المواطن ونائب مجلس النواب',
        'governorates': [], # No longer fetching governorates here
        'site_stats': stats,
        'STATIC_URL': settings.STATIC_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }

