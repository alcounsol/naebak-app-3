from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.core.utils import get_governorate_by_id

register = template.Library()

@register.simple_tag(takes_context=True)
def breadcrumbs(context):
    """
    Generate breadcrumbs based on current URL and context
    """
    request = context['request']
    path = request.path
    breadcrumb_items = []
    
    # Always start with home
    breadcrumb_items.append({
        'title': 'الرئيسية',
        'url': reverse('naebak:home'),
        'is_current': path == reverse('naebak:home')
    })
    
    # Define breadcrumb patterns
    if path.startswith('/governorates/'):
        breadcrumb_items.append({
            'title': 'المحافظات',
            'url': reverse('naebak:governorates'),
            'is_current': path == reverse('naebak:governorates')
        })
        
        # Check for specific governorate
        if 'governorate_slug' in context:
            gov_slug = context['governorate_slug']
            breadcrumb_items.append({
                'title': f'محافظة {gov_slug}',
                'url': f'/governorate/{gov_slug}/',
                'is_current': True
            })
    
    elif path.startswith('/candidates/'):
        breadcrumb_items.append({
            'title': 'المرشحين',
            'url': reverse('naebak:candidates'),
            'is_current': path == reverse('naebak:candidates')
        })
    
    elif path.startswith('/candidate/'):
        breadcrumb_items.append({
            'title': 'المرشحين',
            'url': reverse('naebak:candidates'),
            'is_current': False
        })
        
        if 'candidate' in context:
            candidate = context['candidate']
            breadcrumb_items.append({
                'title': candidate.full_name,
                'url': f'/candidate/{candidate.id}/',
                'is_current': True
            })
    
    elif path.startswith('/admin-panel/'):
        breadcrumb_items.append({
            'title': 'لوحة التحكم',
            'url': reverse('naebak:admin_panel'),
            'is_current': path == reverse('naebak:admin_panel')
        })
        
        # Admin sub-pages
        if 'users' in path:
            breadcrumb_items.append({
                'title': 'إدارة المستخدمين',
                'url': reverse('naebak:user_management'),
                'is_current': True
            })
        elif 'candidates' in path:
            breadcrumb_items.append({
                'title': 'إدارة المرشحين',
                'url': reverse('naebak:manage_candidates'),
                'is_current': True
            })
        elif 'news' in path:
            breadcrumb_items.append({
                'title': 'إدارة الأخبار',
                'url': reverse('naebak:news_management'),
                'is_current': True
            })
        elif 'activity' in path:
            breadcrumb_items.append({
                'title': 'مراقبة النشاط',
                'url': reverse('naebak:activity_monitoring'),
                'is_current': True
            })
        elif 'reports' in path:
            breadcrumb_items.append({
                'title': 'التقارير والإحصائيات',
                'url': reverse('naebak:reports_dashboard'),
                'is_current': True
            })
    
    elif path.startswith('/candidate-dashboard/'):
        breadcrumb_items.append({
            'title': 'لوحة تحكم المرشح',
            'url': reverse('naebak:candidate_dashboard'),
            'is_current': path == reverse('naebak:candidate_dashboard')
        })
        
        # Candidate sub-pages
        if 'profile-edit' in path:
            breadcrumb_items.append({
                'title': 'تعديل الملف الشخصي',
                'url': reverse('naebak:candidate_profile_edit'),
                'is_current': True
            })
        elif 'electoral-program' in path:
            breadcrumb_items.append({
                'title': 'البرنامج الانتخابي',
                'url': reverse('naebak:candidate_electoral_program'),
                'is_current': True
            })
        elif 'promises' in path:
            breadcrumb_items.append({
                'title': 'الوعود الانتخابية',
                'url': reverse('naebak:candidate_promises'),
                'is_current': True
            })
        elif 'messages' in path:
            breadcrumb_items.append({
                'title': 'الرسائل الواردة',
                'url': reverse('naebak:candidate_messages'),
                'is_current': True
            })
        elif 'ratings-votes' in path:
            breadcrumb_items.append({
                'title': 'التقييمات والتصويتات',
                'url': reverse('naebak:candidate_ratings_votes'),
                'is_current': True
            })
    
    elif path == '/profile/':
        breadcrumb_items.append({
            'title': 'الملف الشخصي',
            'url': reverse('naebak:citizen_profile'),
            'is_current': True
        })
    
    elif path == '/my-messages/':
        breadcrumb_items.append({
            'title': 'رسائلي',
            'url': reverse('naebak:my_messages'),
            'is_current': True
        })
    
    elif path == '/privacy-policy/':
        breadcrumb_items.append({
            'title': 'سياسة الخصوصية',
            'url': reverse('naebak:privacy_policy'),
            'is_current': True
        })
    
    elif path == '/terms-of-service/':
        breadcrumb_items.append({
            'title': 'شروط الاستخدام',
            'url': reverse('naebak:terms_of_service'),
            'is_current': True
        })
    
    # Generate HTML
    html = '<nav class="breadcrumb-nav" aria-label="مسار التنقل">'
    html += '<ol class="breadcrumb-list">'
    
    for i, item in enumerate(breadcrumb_items):
        is_last = i == len(breadcrumb_items) - 1
        
        html += '<li class="breadcrumb-item'
        if item['is_current'] or is_last:
            html += ' current'
        html += '">'
        
        if not (item['is_current'] or is_last):
            html += f'<a href="{item["url"]}" class="breadcrumb-link">{item["title"]}</a>'
        else:
            html += f'<span class="breadcrumb-current">{item["title"]}</span>'
        
        if not is_last:
            html += '<span class="breadcrumb-separator">›</span>'
        
        html += '</li>'
    
    html += '</ol>'
    html += '</nav>'
    
    return mark_safe(html)

@register.simple_tag
def breadcrumb_json_ld(breadcrumb_items):
    """
    Generate JSON-LD structured data for breadcrumbs
    """
    if not breadcrumb_items:
        return ""
    
    json_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }
    
    for i, item in enumerate(breadcrumb_items, 1):
        json_ld["itemListElement"].append({
            "@type": "ListItem",
            "position": i,
            "name": item['title'],
            "item": f"https://naebak.com{item['url']}"
        })
    
    import json
    return mark_safe(f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>')

