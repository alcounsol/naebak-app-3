"""
معالجات السياق (Context Processors) لتطبيق core
توفر متغيرات عامة لجميع القوالب
"""

from django.conf import settings
from apps.candidates.models import Candidate
from apps.accounts.models import Citizen


def site_context(request):
    """
    معالج السياق الرئيسي للموقع
    يوفر المتغيرات العامة المطلوبة في جميع القوالب
    """
    
    # إحصائيات الموقع
    try:
        stats = {
            'total_governorates': 27,  # Fixed number of Egyptian governorates
            'total_candidates': Candidate.objects.count(),
            'total_voters': Citizen.objects.count(),
            'online_visitors': 0,  # Can be implemented with sessions/cache
        }
    except:
        stats = {
            'total_governorates': 27,
            'total_candidates': 0,
            'total_voters': 0,
            'online_visitors': 0,
        }
    
    # Add ticker news if available
    ticker_news = []
    try:
        from apps.news.models import News
        ticker_news = News.get_ticker_news()[:5]
    except:
        pass
    
    return {
        'site_name': 'نائبك دوت كوم',
        'site_description': 'حلقة الوصل بين المواطن ونائب مجلس النواب في جمهورية مصر العربية',
        'site_stats': stats,
        'ticker_news': ticker_news,
        'current_year': 2024,
        'STATIC_URL': settings.STATIC_URL,
        'MEDIA_URL': settings.MEDIA_URL,
    }

