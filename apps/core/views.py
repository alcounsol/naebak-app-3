"""
Core views for the main application functionality
"""

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST, require_GET

# Import models from their respective apps
from apps.candidates.models import Candidate, ElectoralPromise, PublicServiceHistory, FeaturedCandidate
from apps.messaging.models import Message
from apps.voting.models import Rating, Vote
from apps.news.models import News
from apps.accounts.models import Citizen
from .models import ActivityLog
from .utils import load_governorates_data, get_governorate_by_id, get_governorate_by_slug, search_governorates

import json
import os
from django.conf import settings


def home(request):
    """
    الصفحة الرئيسية للموقع (Landing Page)
    """
    featured_candidates = Candidate.objects.filter(is_featured=True).order_by("name")[:6]
    
    # Get latest news for ticker
    latest_news = News.get_ticker_news()[:5]
    
    context = {
        'page_title': 'الصفحة الرئيسية',
        'meta_description': 'نائبك دوت كوم - حلقة الوصل بين المواطن ونائب مجلس النواب في جمهورية مصر العربية',
        'featured_candidates': featured_candidates,
        'latest_news': latest_news,
    }
    return render(request, 'core/index.html', context)

def governorates(request):
    """
    صفحة قائمة المحافظات مع البحث المتقدم - تستخدم ملف JSON
    """
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'name')  # name, candidates_count, activity
    
    # Load governorates from JSON
    if search_query:
        governorates_list = search_governorates(search_query)
    else:
        governorates_list = load_governorates_data()
    
    # Calculate statistics for each governorate
    governorates_with_stats = []
    for governorate in governorates_list:
        # Get candidates for this governorate
        candidates = Candidate.objects.filter(governorate_id=governorate['id'])
        total_candidates = candidates.count()
        
        # Calculate total activity
        total_messages = sum(c.messages.count() for c in candidates)
        total_votes = sum(c.votes.count() for c in candidates)
        total_ratings = sum(c.ratings.count() for c in candidates)
        total_activity = total_messages + total_votes + total_ratings
        
        # Calculate average rating for governorate
        all_ratings = []
        for candidate in candidates:
            candidate_ratings = candidate.ratings.all()
            if candidate_ratings.exists():
                avg_rating = sum(r.stars for r in candidate_ratings) / len(candidate_ratings)
                all_ratings.append(avg_rating)
        
        avg_governorate_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
        
        # Get total citizens for this governorate
        total_citizens = Citizen.objects.filter(governorate_id=governorate["id"]).count()
        
        governorates_with_stats.append({
            'governorate': governorate,
            'total_candidates': total_candidates,
            'total_messages': total_messages,
            'total_votes': total_votes,
            'total_ratings': total_ratings,
            'total_activity': total_activity,
            'avg_rating': round(avg_governorate_rating, 1),
            'total_citizens': total_citizens,
        })
    
    # Apply sorting
    if sort_by == 'candidates_count':
        governorates_with_stats.sort(key=lambda x: x['total_candidates'], reverse=True)
    elif sort_by == 'activity':
        governorates_with_stats.sort(key=lambda x: x['total_activity'], reverse=True)
    else:
        # Default sort by name
        governorates_with_stats.sort(key=lambda x: x['governorate']['name_ar'])
    
    context = {
        'page_title': 'المحافظات',
        'governorates_with_stats': governorates_with_stats,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_governorates': len(governorates_with_stats),
    }
    return render(request, 'core/governorates.html', context)


def governorate_detail(request, governorate_slug):
    """
    صفحة تفاصيل محافظة معينة مع قائمة المرشحين
    """
    # Get governorate data from JSON
    governorate = get_governorate_by_slug(governorate_slug)
    if not governorate:
        messages.error(request, 'المحافظة المطلوبة غير موجودة.')
        return redirect('core:governorates')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'name')  # name, rating, votes, activity
    
    # Get candidates for this governorate
    candidates = Candidate.objects.filter(governorate_id=governorate['id'])
    
    # Apply search filter
    if search_query:
        candidates = candidates.filter(
            Q(name__icontains=search_query) |
            Q(constituency__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(electoral_program__icontains=search_query)
        )
    
    # Calculate statistics for each candidate
    candidates_with_stats = []
    for candidate in candidates:
        # Calculate statistics
        total_votes = candidate.votes.count()
        approve_votes = candidate.votes.filter(vote_type='approve').count()
        disapprove_votes = candidate.votes.filter(vote_type='disapprove').count()
        
        ratings = candidate.ratings.all()
        avg_rating = ratings.aggregate(Avg('stars'))['stars__avg'] or 0
        total_ratings = ratings.count()
        
        total_messages = candidate.messages.count()
        total_activity = total_votes + total_ratings + total_messages
        
        candidates_with_stats.append({
            'candidate': candidate,
            'total_votes': total_votes,
            'approve_votes': approve_votes,
            'disapprove_votes': disapprove_votes,
            'avg_rating': round(avg_rating, 1),
            'total_ratings': total_ratings,
            'total_messages': total_messages,
            'total_activity': total_activity,
        })
    
    # Apply sorting
    if sort_by == 'rating':
        candidates_with_stats.sort(key=lambda x: x['avg_rating'], reverse=True)
    elif sort_by == 'votes':
        candidates_with_stats.sort(key=lambda x: x['total_votes'], reverse=True)
    elif sort_by == 'activity':
        candidates_with_stats.sort(key=lambda x: x['total_activity'], reverse=True)
    else:
        # Default sort by name
        candidates_with_stats.sort(key=lambda x: x['candidate'].name)
    
    # Pagination
    paginator = Paginator(candidates_with_stats, 12)  # Show 12 candidates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': f'مرشحو {governorate["name_ar"]}',
        'governorate': governorate,
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_candidates': len(candidates_with_stats),
    }
    return render(request, 'core/governorate_detail.html', context)


@login_required
def citizen_login_required(request):
    """
    Decorator view to ensure user has citizen profile
    """
    try:
        citizen = request.user.citizen_profile
        return None  # User has citizen profile
    except Citizen.DoesNotExist:
        messages.error(request, 'يجب إنشاء ملف شخصي للمواطن أولاً.')
        return redirect('accounts:citizen_register')


def about(request):
    """
    صفحة حول الموقع
    """
    context = {
        'page_title': 'حول الموقع',
        'meta_description': 'تعرف على موقع نائبك دوت كوم ورسالته في ربط المواطن بنائب مجلس النواب',
    }
    return render(request, 'naebak/about.html', context)


def contact(request):
    """
    صفحة اتصل بنا
    """
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if name and email and subject and message:
            # Log the contact attempt
            ActivityLog.log_activity(
                user=request.user if request.user.is_authenticated else None,
                action_type='contact_form',
                description=f'رسالة اتصال من {name} ({email}): {subject}',
                extra_data={
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'message': message,
                }
            )
            
            messages.success(request, 'تم إرسال رسالتك بنجاح. سنتواصل معك قريباً.')
            return redirect('core:contact')
        else:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
    
    context = {
        'page_title': 'اتصل بنا',
        'meta_description': 'تواصل مع فريق نائبك دوت كوم',
    }
    return render(request, 'naebak/contact.html', context)


def privacy_policy(request):
    """
    صفحة سياسة الخصوصية
    """
    context = {
        'page_title': 'سياسة الخصوصية',
        'meta_description': 'سياسة الخصوصية لموقع نائبك دوت كوم',
    }
    return render(request, 'naebak/privacy_policy.html', context)


def terms_of_service(request):
    """
    صفحة شروط الخدمة
    """
    context = {
        'page_title': 'شروط الخدمة',
        'meta_description': 'شروط استخدام موقع نائبك دوت كوم',
    }
    return render(request, 'naebak/terms_of_service.html', context)


# API Views for AJAX requests
@require_GET
def api_governorates_search(request):
    """
    API endpoint for governorate search autocomplete
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    governorates = search_governorates(query)[:10]  # Limit to 10 results
    
    results = []
    for gov in governorates:
        results.append({
            'id': gov['id'],
            'name': gov['name_ar'],
            'slug': gov['slug'],
            'name_en': gov['name_en'],
        })
    
    return JsonResponse({'results': results})


@require_GET
def api_candidates_search(request):
    """
    API endpoint for candidate search autocomplete
    """
    query = request.GET.get('q', '').strip()
    governorate_id = request.GET.get('governorate_id')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    candidates = Candidate.objects.filter(
        Q(name__icontains=query) |
        Q(constituency__icontains=query)
    )
    
    if governorate_id:
        candidates = candidates.filter(governorate_id=governorate_id)
    
    candidates = candidates[:10]  # Limit to 10 results
    
    results = []
    for candidate in candidates:
        results.append({
            'id': candidate.id,
            'name': candidate.name,
            'constituency': candidate.constituency,
            'governorate_name': candidate.governorate_name,
        })
    
    return JsonResponse({'results': results})



@login_required
def profile_view(request):
    """
    صفحة الملف الشخصي للمستخدم
    """
    context = {
        'page_title': 'الملف الشخصي',
        'meta_description': 'الملف الشخصي للمستخدم على موقع نائبك دوت كوم',
    }
    return render(request, 'accounts/profile.html', context)










def logout_view(request):
    """
    تسجيل خروج المستخدم
    """
    logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect("core:home")






