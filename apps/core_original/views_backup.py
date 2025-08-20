"""
Views لتطبيق naebak الرئيسي
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
from .models import Candidate, ElectoralPromise, PublicServiceHistory, Message, Rating, Vote, News, ActivityLog
from .utils import load_governorates_data, get_governorate_by_id, get_governorate_by_slug, search_governorates
import json
import os
from django.conf import settings


def home(request):
    """
    الصفحة الرئيسية للموقع (Landing Page)
    """
    context = {
        'page_title': 'الصفحة الرئيسية',
        'meta_description': 'نائبك دوت كوم - حلقة الوصل بين المواطن ونائب مجلس النواب في جمهورية مصر العربية',
    }
    return render(request, 'naebak/index.html', context)


def governorates(request):
    """
    صفحة قائمة المحافظات مع البحث المتقدم
    """
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'name')  # name, candidates_count, activity
    
    # Start with all governorates
    governorates_list = Governorate.objects.prefetch_related('candidates').all()
    
    # Apply search filter
    if search_query:
        governorates_list = governorates_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'candidates_count':
        # Sort by number of candidates
        governorates_list = governorates_list.annotate(
            candidates_count=Count('candidates')
        ).order_by('-candidates_count', 'name')
    elif sort_by == 'activity':
        # Sort by total activity (messages + votes + ratings)
        governorates_list = governorates_list.annotate(
            total_messages=Count('candidates__messages'),
            total_votes=Count('candidates__votes'),
            total_ratings=Count('candidates__ratings'),
            total_activity=Count('candidates__messages') + Count('candidates__votes') + Count('candidates__ratings')
        ).order_by('-total_activity', 'name')
    else:
        # Default sort by name
        governorates_list = governorates_list.order_by('name')
    
    # Calculate statistics for each governorate
    governorates_with_stats = []
    for governorate in governorates_list:
        candidates = governorate.candidates.all()
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
        
        governorates_with_stats.append({
            'governorate': governorate,
            'total_candidates': total_candidates,
            'total_messages': total_messages,
            'total_votes': total_votes,
            'total_ratings': total_ratings,
            'total_activity': total_activity,
            'avg_rating': round(avg_governorate_rating, 1),
        })
    
    context = {
        'page_title': 'المحافظات',
        'governorates_with_stats': governorates_with_stats,
        'search_query': search_query,
        'sort_by': sort_by,
        'total_governorates': len(governorates_with_stats),
    }
    return render(request, 'naebak/governorates.html', context)


def governorate_detail(request, slug):
    governorate = get_object_or_404(Governorate, slug=slug)
    featured_candidates = governorate.candidates.filter(is_featured=True)[:6]
    other_candidates = governorate.candidates.filter(is_featured=False)
    featured_votes = governorate.featured_votes.all()[:4]

    context = {
        'page_title': f'محافظة {governorate.name}',
        'governorate': governorate,
        'featured_candidates': featured_candidates,
        'other_candidates': other_candidates,
        'featured_votes': featured_votes,
    }
    return render(request, 'naebak/governorate_detail.html', context)


def candidates(request):
    """
    صفحة عرض جميع المرشحين مع البحث المتقدم
    """
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    governorate_filter = request.GET.get('governorate', '')
    constituency_filter = request.GET.get('constituency', '')
    sort_by = request.GET.get('sort', 'name')  # name, rating, votes, messages
    
    # Start with all candidates
    candidates_list = Candidate.objects.select_related('governorate').prefetch_related(
        'ratings', 'votes', 'messages', 'electoral_promises'
    ).all()
    
    # Apply search filter
    if search_query:
        candidates_list = candidates_list.filter(
            Q(name__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(electoral_program__icontains=search_query) |
            Q(message_to_voters__icontains=search_query) |
            Q(constituency__icontains=search_query) |
            Q(election_symbol__icontains=search_query)
        )
    
    # Apply governorate filter
    if governorate_filter:
        candidates_list = candidates_list.filter(governorate__id=governorate_filter)
    
    # Apply constituency filter
    if constituency_filter:
        candidates_list = candidates_list.filter(constituency__icontains=constituency_filter)
    
    # Apply sorting
    if sort_by == 'rating':
        # Sort by average rating (requires annotation)
        candidates_list = candidates_list.annotate(
            avg_rating=Avg('ratings__stars')
        ).order_by('-avg_rating', 'name')
    elif sort_by == 'votes':
        # Sort by total votes
        candidates_list = candidates_list.annotate(
            total_votes=Count('votes')
        ).order_by('-total_votes', 'name')
    elif sort_by == 'messages':
        # Sort by total messages
        candidates_list = candidates_list.annotate(
            total_messages=Count('messages')
        ).order_by('-total_messages', 'name')
    else:
        # Default sort by name
        candidates_list = candidates_list.order_by('name')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(candidates_list, 12)  # 12 candidates per page
    page_number = request.GET.get('page')
    candidates_page = paginator.get_page(page_number)
    
    # Get all governorates for filter dropdown
    governorates = Governorate.objects.all().order_by('name')
    
    # Get unique constituencies for filter
    constituencies = Candidate.objects.values_list('constituency', flat=True).distinct().exclude(constituency__isnull=True).exclude(constituency__exact='')
    constituencies = sorted([c for c in constituencies if c])
    
    # Calculate statistics for each candidate
    candidates_with_stats = []
    for candidate in candidates_page:
        # Calculate average rating
        ratings = candidate.ratings.all()
        avg_rating = 0
        if ratings.exists():
            avg_rating = sum(r.stars for r in ratings) / len(ratings)
        
        # Calculate vote statistics
        votes = candidate.votes.all()
        total_votes = votes.count()
        approve_votes = votes.filter(vote_type='approve').count()
        approval_rate = (approve_votes / total_votes * 100) if total_votes > 0 else 0
        
        candidates_with_stats.append({
            'candidate': candidate,
            'avg_rating': round(avg_rating, 1),
            'total_votes': total_votes,
            'approval_rate': round(approval_rate, 1),
            'total_messages': candidate.messages.count(),
            'total_promises': candidate.electoral_promises.count(),
        })
    
    # Update the page object with our enhanced data
    candidates_page.object_list = candidates_with_stats
    
    context = {
        'page_title': 'المرشحون',
        'candidates_page': candidates_page,
        'governorates': governorates,
        'constituencies': constituencies,
        'search_query': search_query,
        'governorate_filter': governorate_filter,
        'constituency_filter': constituency_filter,
        'sort_by': sort_by,
        'total_candidates': paginator.count,
    }
    return render(request, 'naebak/candidates.html', context)


def candidate_profile(request):
    """
    صفحة الملف الشخصي للمرشح
    """
    context = {
        'page_title': 'الملف الشخصي للمرشح',
    }
    return render(request, 'naebak/candidate_profile.html', context)


def candidate_detail(request, pk):
    """
    صفحة تفاصيل المرشح
    """
    try:
        candidate = Candidate.objects.get(id=pk)
    except Candidate.DoesNotExist:
        messages.error(request, 'المرشح غير موجود.')
        return redirect('naebak:candidates')
    
    # Get related data
    electoral_promises = candidate.electoral_promises.all().order_by('order')
    service_history = candidate.service_history.all().order_by('-start_year')
    recent_ratings = candidate.ratings.all().order_by('-timestamp')[:5]
    
    # Calculate average rating
    ratings = candidate.ratings.all()
    average_rating = 0
    if ratings.exists():
        total_stars = sum(rating.stars for rating in ratings)
        average_rating = total_stars / ratings.count()
    
    # Calculate voting statistics
    votes = candidate.votes.all()
    total_votes = votes.count()
    approve_votes = votes.filter(vote_type='approve').count()
    disapprove_votes = votes.filter(vote_type='disapprove').count()
    
    approval_rate = 0
    disapproval_rate = 0
    if total_votes > 0:
        approval_rate = (approve_votes / total_votes) * 100
        disapproval_rate = (disapprove_votes / total_votes) * 100
    
    # Process YouTube URL for embedding
    youtube_embed_url = None
    if candidate.youtube_url:
        # Convert YouTube URL to embed format
        if 'youtube.com/watch?v=' in candidate.youtube_url:
            video_id = candidate.youtube_url.split('watch?v=')[1].split('&')[0]
            youtube_embed_url = f"https://www.youtube.com/embed/{video_id}"
        elif 'youtu.be/' in candidate.youtube_url:
            video_id = candidate.youtube_url.split('youtu.be/')[1].split('?')[0]
            youtube_embed_url = f"https://www.youtube.com/embed/{video_id}"
        else:
            youtube_embed_url = candidate.youtube_url
    
    context = {
        'page_title': f'الملف الشخصي - {candidate.name}',
        'candidate': candidate,
        'electoral_promises': electoral_promises,
        'service_history': service_history,
        'recent_ratings': recent_ratings,
        'average_rating': average_rating,
        'total_votes': total_votes,
        'approve_votes': approve_votes,
        'disapprove_votes': disapprove_votes,
        'approval_rate': approval_rate,
        'disapproval_rate': disapproval_rate,
        'youtube_embed_url': youtube_embed_url,
    }
    return render(request, 'naebak/candidate_detail.html', context)


def news(request):
    """
    صفحة قائمة الأخبار
    """
    context = {
        'page_title': 'الأخبار',
    }
    return render(request, 'naebak/news.html', context)


def news_detail(request, pk):
    """
    صفحة تفاصيل الخبر
    """
    context = {
        'page_title': 'تفاصيل الخبر',
        'news_id': pk,
    }
    return render(request, 'naebak/news_detail.html', context)


def conversations(request):
    """
    صفحة المحادثات
    """
    context = {
        'page_title': 'المحادثات',
    }
    return render(request, 'naebak/conversations.html', context)


def citizen_register(request):
    """
    صفحة تسجيل المواطن
    """
    if request.method == 'POST':
        # سيتم تطوير منطق التسجيل لاحقاً
        messages.success(request, 'تم تسجيل البيانات بنجاح')
        return redirect('naebak:profile')
    
    context = {
        'page_title': 'تسجيل مواطن جديد',
    }
    return render(request, 'naebak/register.html', context)


@login_required
def citizen_profile(request):
    """
    صفحة ملف المواطن الشخصي
    """
    user = request.user
    
    # Get user's voting history
    user_votes = Vote.objects.filter(citizen=user).select_related('candidate').order_by('-timestamp')[:10]
    
    # Get user's rating history
    user_ratings = Rating.objects.filter(citizen=user).select_related('candidate').order_by('-timestamp')[:10]
    
    # Get user's sent messages
    user_messages = Message.objects.filter(sender_user=user).select_related('candidate').order_by('-timestamp')[:10]
    
    # Calculate statistics
    total_votes = Vote.objects.filter(citizen=user).count()
    total_ratings = Rating.objects.filter(citizen=user).count()
    total_messages = Message.objects.filter(sender_user=user).count()
    
    # Calculate vote breakdown
    approve_votes = Vote.objects.filter(citizen=user, vote_type='approve').count()
    disapprove_votes = Vote.objects.filter(citizen=user, vote_type='disapprove').count()
    
    # Calculate average rating given by user
    user_ratings_avg = user_ratings.aggregate(Avg('stars'))['stars__avg'] or 0
    
    context = {
        'page_title': 'ملفي الشخصي',
        'user_profile': user,
        'user_votes': user_votes,
        'user_ratings': user_ratings,
        'user_messages': user_messages,
        'total_votes': total_votes,
        'total_ratings': total_ratings,
        'total_messages': total_messages,
        'approve_votes': approve_votes,
        'disapprove_votes': disapprove_votes,
        'user_ratings_avg': round(user_ratings_avg, 1),
    }
    return render(request, 'naebak/profile.html', context)

@login_required
def admin_panel(request):
    """
    لوحة تحكم الأدمن الرئيسي
    """
    # التحقق من صلاحيات الأدمن الرئيسي
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('naebak:home')
    
    # Get statistics
    total_users = User.objects.count()
    total_candidates = Candidate.objects.count()
    total_governorates = Governorate.objects.count()
    total_messages = Message.objects.count()
    
    context = {
        'page_title': 'لوحة تحكم الأدمن الرئيسي',
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_governorates': total_governorates,
        'total_messages': total_messages,
    }
    return render(request, 'naebak/admin_panel.html', context)



def user_login(request):
    """
    صفحة تسجيل الدخول
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Check if user is a candidate and redirect to candidate dashboard
            try:
                candidate = user.candidate_profile
                messages.success(request, f'مرحباً {candidate.name}')
                return redirect('naebak:candidate_dashboard')
            except Candidate.DoesNotExist:
                # Regular user, redirect to home or next URL
                next_url = request.GET.get('next', 'naebak:home')
                return redirect(next_url)
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    
    context = {
        'page_title': 'تسجيل الدخول',
    }
    return render(request, 'naebak/login.html', context)


def user_logout(request):
    """
    تسجيل الخروج
    """
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح')
    return redirect('naebak:home')


@cache_page(60 * 60)  # كاش لمدة ساعة
def robots_txt(request):
    """
    ملف robots.txt
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /api/",
        "",
        "Sitemap: https://naebak.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# Candidate Dashboard Views
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, Http404
import json
import os

from .models import Candidate, ElectoralPromise, PublicServiceHistory, Message, Rating, RatingReply, Vote, Governorate, FeaturedVote
from django.db.models import Avg


@login_required
def candidate_dashboard(request):
    """Main dashboard view for candidates"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح. يرجى التواصل مع الإدارة.')
        return redirect('naebak:login')
    
    # Get dashboard statistics
    total_messages = candidate.messages.count()
    unread_messages = candidate.messages.filter(is_read=False).count()
    total_ratings = candidate.ratings.count()
    unread_ratings = candidate.ratings.filter(is_read=False).count()
    
    # Get voting statistics
    total_votes = candidate.votes.count()
    approve_votes = candidate.votes.filter(vote_type='approve').count()
    disapprove_votes = candidate.votes.filter(vote_type='disapprove').count()
    
    approval_percentage = (approve_votes / total_votes * 100) if total_votes > 0 else 0
    
    # Get recent activity
    recent_messages = candidate.messages.all()[:5]
    recent_ratings = candidate.ratings.all()[:5]
    
    context = {
        'candidate': candidate,
        'total_messages': total_messages,
        'unread_messages': unread_messages,
        'total_ratings': total_ratings,
        'unread_ratings': unread_ratings,
        'total_votes': total_votes,
        'approve_votes': approve_votes,
        'disapprove_votes': disapprove_votes,
        'approval_percentage': round(approval_percentage, 2),
        'recent_messages': recent_messages,
        'recent_ratings': recent_ratings,
    }
    return render(request, 'naebak/candidate_dashboard.html', context)


@login_required
def profile_management(request):
    """View for managing candidate profile information"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح.')
        return redirect('naebak:candidate_dashboard')
    
    if request.method == 'POST':
        # Update basic information
        candidate.name = request.POST.get('name', candidate.name)
        candidate.role = request.POST.get('role', candidate.role)
        candidate.constituency = request.POST.get('constituency', candidate.constituency)
        candidate.bio = request.POST.get('bio', candidate.bio)
        
        # Handle file uploads
        if 'profile_picture' in request.FILES:
            candidate.profile_picture = request.FILES['profile_picture']
        
        if 'banner_image' in request.FILES:
            candidate.banner_image = request.FILES['banner_image']
        
        candidate.save()
        messages.success(request, 'تم تحديث الملف الشخصي بنجاح.')
        return redirect('naebak:profile_management')
    
    context = {
        'candidate': candidate,
    }
    return render(request, 'naebak/profile_management.html', context)


@login_required
def electoral_program_management(request):
    """View for managing electoral promises"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح.')
        return redirect('naebak:candidate_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            title = request.POST.get('title')
            description = request.POST.get('description')
            order = request.POST.get('order', 0)
            
            if title and description:
                ElectoralPromise.objects.create(
                    candidate=candidate,
                    title=title,
                    description=description,
                    order=int(order) if order else 0
                )
                messages.success(request, 'تم إضافة الوعد الانتخابي بنجاح.')
            else:
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
        
        elif action == 'edit':
            promise_id = request.POST.get('promise_id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            order = request.POST.get('order', 0)
            
            try:
                promise = ElectoralPromise.objects.get(id=promise_id, candidate=candidate)
                promise.title = title
                promise.description = description
                promise.order = int(order) if order else 0
                promise.save()
                messages.success(request, 'تم تحديث الوعد الانتخابي بنجاح.')
            except ElectoralPromise.DoesNotExist:
                messages.error(request, 'لم يتم العثور على الوعد الانتخابي.')
        
        elif action == 'delete':
            promise_id = request.POST.get('promise_id')
            try:
                promise = ElectoralPromise.objects.get(id=promise_id, candidate=candidate)
                promise.delete()
                messages.success(request, 'تم حذف الوعد الانتخابي بنجاح.')
            except ElectoralPromise.DoesNotExist:
                messages.error(request, 'لم يتم العثور على الوعد الانتخابي.')
        
        return redirect('naebak:electoral_program_management')
    
    promises = candidate.electoral_promises.all()
    
    context = {
        'candidate': candidate,
        'promises': promises,
    }
    return render(request, 'naebak/electoral_program_management.html', context)


@login_required
def service_history_management(request):
    """View for managing public service history"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح.')
        return redirect('naebak:candidate_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            start_year = request.POST.get('start_year')
            end_year = request.POST.get('end_year')
            position = request.POST.get('position')
            description = request.POST.get('description')
            
            if start_year and end_year and position and description:
                PublicServiceHistory.objects.create(
                    candidate=candidate,
                    start_year=int(start_year),
                    end_year=int(end_year),
                    position=position,
                    description=description
                )
                messages.success(request, 'تم إضافة التاريخ في العمل العام بنجاح.')
            else:
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
        
        elif action == 'edit':
            history_id = request.POST.get('history_id')
            start_year = request.POST.get('start_year')
            end_year = request.POST.get('end_year')
            position = request.POST.get('position')
            description = request.POST.get('description')
            
            try:
                history = PublicServiceHistory.objects.get(id=history_id, candidate=candidate)
                history.start_year = int(start_year)
                history.end_year = int(end_year)
                history.position = position
                history.description = description
                history.save()
                messages.success(request, 'تم تحديث التاريخ في العمل العام بنجاح.')
            except PublicServiceHistory.DoesNotExist:
                messages.error(request, 'لم يتم العثور على السجل.')
        
        elif action == 'delete':
            history_id = request.POST.get('history_id')
            try:
                history = PublicServiceHistory.objects.get(id=history_id, candidate=candidate)
                history.delete()
                messages.success(request, 'تم حذف السجل بنجاح.')
            except PublicServiceHistory.DoesNotExist:
                messages.error(request, 'لم يتم العثور على السجل.')
        
        return redirect('naebak:service_history_management')
    
    service_history = candidate.service_history.all()
    
    context = {
        'candidate': candidate,
        'service_history': service_history,
    }
    return render(request, 'naebak/service_history_management.html', context)


@login_required
def messages_management(request):
    """View for managing messages from citizens"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح.')
        return redirect('naebak:candidate_dashboard')
    
    # Filter messages
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    
    messages_queryset = candidate.messages.filter(reply_to__isnull=True)  # Only parent messages
    
    if filter_type == 'unread':
        messages_queryset = messages_queryset.filter(is_read=False)
    elif filter_type == 'read':
        messages_queryset = messages_queryset.filter(is_read=True)
    
    if search_query:
        messages_queryset = messages_queryset.filter(
            Q(subject__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(sender_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(messages_queryset, 10)
    page_number = request.GET.get('page')
    page_messages = paginator.get_page(page_number)
    
    context = {
        'candidate': candidate,
        'messages': page_messages,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    return render(request, 'naebak/messages_management.html', context)


@login_required
def message_detail(request, message_id):
    """View for detailed message view and reply"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح.')
        return redirect('naebak:candidate_dashboard')
    
    try:
        message = Message.objects.get(id=message_id, candidate=candidate)
    except Message.DoesNotExist:
        messages.error(request, 'لم يتم العثور على الرسالة.')
        return redirect('naebak:messages_management')
    
    # Mark as read
    if not message.is_read:
        message.is_read = True
        message.save()
    
    if request.method == 'POST':
        reply_content = request.POST.get('reply_content')
        if reply_content:
            Message.objects.create(
                candidate=candidate,
                sender_user=request.user,
                sender_name=candidate.name,
                sender_email='',
                subject=f"رد: {message.subject}",
                content=reply_content,
                reply_to=message,
                is_read=True  # Candidate's own reply is marked as read
            )
            messages.success(request, 'تم إرسال الرد بنجاح.')
            return redirect('naebak:message_detail', message_id=message.id)
    
    # Get all replies to this message
    replies = message.replies.all()
    
    context = {
        'candidate': candidate,
        'message': message,
        'replies': replies,
    }
    return render(request, 'naebak/message_detail.html', context)


@login_required
def download_attachment(request, message_id):
    """View for downloading message attachments"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        raise Http404("Candidate not found")
    
    try:
        message = Message.objects.get(id=message_id, candidate=candidate)
    except Message.DoesNotExist:
        raise Http404("Message not found")
    
    if not message.attachment:
        raise Http404("No attachment found")
    
    # Serve the file
    response = HttpResponse(message.attachment.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(message.attachment.name)}"'
    return response


@login_required
def ratings_management(request):
    """View for managing ratings and comments"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح.')
        return redirect('naebak:candidate_dashboard')
    
    # Filter ratings
    filter_type = request.GET.get('filter', 'all')
    star_filter = request.GET.get('stars', '')
    
    ratings_queryset = candidate.ratings.all()
    
    if filter_type == 'unread':
        ratings_queryset = ratings_queryset.filter(is_read=False)
    elif filter_type == 'read':
        ratings_queryset = ratings_queryset.filter(is_read=True)
    elif filter_type == 'with_comments':
        ratings_queryset = ratings_queryset.exclude(comment='')
    
    if star_filter:
        ratings_queryset = ratings_queryset.filter(stars=int(star_filter))
    
    # Pagination
    paginator = Paginator(ratings_queryset, 10)
    page_number = request.GET.get('page')
    page_ratings = paginator.get_page(page_number)
    
    context = {
        'candidate': candidate,
        'ratings': page_ratings,
        'filter_type': filter_type,
        'star_filter': star_filter,
    }
    return render(request, 'naebak/ratings_management.html', context)


@login_required
def rating_reply(request, rating_id):
    """View for replying to ratings"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح.')
        return redirect('naebak:candidate_dashboard')
    
    try:
        rating = Rating.objects.get(id=rating_id, candidate=candidate)
    except Rating.DoesNotExist:
        messages.error(request, 'لم يتم العثور على التقييم.')
        return redirect('naebak:ratings_management')
    
    # Mark as read
    if not rating.is_read:
        rating.is_read = True
        rating.save()
    
    if request.method == 'POST':
        reply_content = request.POST.get('reply_content')
        if reply_content:
            # Delete existing reply if any
            RatingReply.objects.filter(rating=rating).delete()
            
            # Create new reply
            RatingReply.objects.create(
                rating=rating,
                candidate=candidate,
                content=reply_content
            )
            messages.success(request, 'تم إرسال الرد بنجاح.')
            return redirect('naebak:ratings_management')
    
    context = {
        'candidate': candidate,
        'rating': rating,
    }
    return render(request, 'naebak/rating_reply.html', context)


@login_required
def voting_results(request):
    """View for monitoring voting results"""
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'لم يتم العثور على ملف المرشح.')
        return redirect('naebak:candidate_dashboard')
    
    # Get voting statistics
    total_votes = candidate.votes.count()
    approve_votes = candidate.votes.filter(vote_type='approve').count()
    disapprove_votes = candidate.votes.filter(vote_type='disapprove').count()
    
    approval_percentage = (approve_votes / total_votes * 100) if total_votes > 0 else 0
    disapproval_percentage = (disapprove_votes / total_votes * 100) if total_votes > 0 else 0
    
    # Get recent votes
    recent_votes = candidate.votes.all()[:20]
    
    # Get voting trends (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_approve_votes = candidate.votes.filter(
        vote_type='approve',
        timestamp__gte=thirty_days_ago
    ).count()
    recent_disapprove_votes = candidate.votes.filter(
        vote_type='disapprove',
        timestamp__gte=thirty_days_ago
    ).count()
    
    context = {
        'candidate': candidate,
        'total_votes': total_votes,
        'approve_votes': approve_votes,
        'disapprove_votes': disapprove_votes,
        'approval_percentage': round(approval_percentage, 2),
        'disapproval_percentage': round(disapproval_percentage, 2),
        'recent_votes': recent_votes,
        'recent_approve_votes': recent_approve_votes,
        'recent_disapprove_votes': recent_disapprove_votes,
    }
    return render(request, 'naebak/voting_results.html', context)


def candidate_login(request):
    """Login view for candidates"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user has a candidate profile
            try:
                candidate = user.candidate_profile
                login(request, user)
                messages.success(request, f'مرحباً {candidate.name}')
                return redirect('naebak:candidate_dashboard')
            except Candidate.DoesNotExist:
                messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
    
    return render(request, 'naebak/candidate_login.html')


def candidate_logout(request):
    """Logout view for candidates"""
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح.')
    return redirect('naebak:candidate_login')



# Governorate Views

def governorate_page(request, slug):
    """
    صفحة المحافظة مع المرشحين المميزين والتصويتات المتميزة
    """
    try:
        governorate = get_object_or_404(Governorate, slug=slug)
    except Http404:
        messages.error(request, 'لم يتم العثور على المحافظة المطلوبة.')
        return redirect('naebak:home')
    
    # Get featured candidates (up to 6)
    featured_candidates = Candidate.objects.filter(
        governorate=governorate, 
        is_featured=True
    ).select_related('user').prefetch_related('ratings')[:6]
    
    # Add average rating for each featured candidate
    for candidate in featured_candidates:
        avg_rating = candidate.ratings.aggregate(avg_stars=Avg('stars'))['avg_stars']
        candidate.average_rating = round(avg_rating, 1) if avg_rating else 0
    
    # Get other candidates (not featured, up to 5)
    other_candidates = Candidate.objects.filter(
        governorate=governorate, 
        is_featured=False
    ).select_related('user').prefetch_related('ratings')[:5]
    
    # Add average rating for each other candidate
    for candidate in other_candidates:
        avg_rating = candidate.ratings.aggregate(avg_stars=Avg('stars'))['avg_stars']
        candidate.average_rating = round(avg_rating, 1) if avg_rating else 0
    
    # Get all candidates for statistics
    all_candidates = Candidate.objects.filter(governorate=governorate)
    
    # Get featured votes (up to 4)
    featured_votes = FeaturedVote.objects.filter(
        governorate=governorate
    ).select_related('candidate').order_by('order', '-created_at')[:4]
    
    # Add vote counts for each featured vote
    for vote in featured_votes:
        vote.title = f"تصويت على {vote.get_vote_type_display()}"
        vote.yes_votes = Vote.objects.filter(candidate=vote.candidate, vote_type='approve').count()
        vote.no_votes = Vote.objects.filter(candidate=vote.candidate, vote_type='disapprove').count()
    
    context = {
        'page_title': f'محافظة {governorate.name}',
        'governorate': governorate,
        'featured_candidates': featured_candidates,
        'other_candidates': other_candidates,
        'all_candidates': all_candidates,
        'featured_votes': featured_votes,
        'meta_description': f'صفحة محافظة {governorate.name} - تعرف على مرشحي المحافظة وتصويتاتهم',
    }
    return render(request, 'naebak/governorate_page.html', context)


def governorate_candidates_list(request, slug):
    """
    صفحة قائمة جميع مرشحي المحافظة
    """
    try:
        governorate = get_object_or_404(Governorate, slug=slug)
    except Http404:
        messages.error(request, 'لم يتم العثور على المحافظة المطلوبة.')
        return redirect('naebak:home')
    
    # Get all candidates for this governorate
    candidates_queryset = Candidate.objects.filter(
        governorate=governorate
    ).select_related('user').prefetch_related('ratings')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        candidates_queryset = candidates_queryset.filter(
            Q(name__icontains=search_query) |
            Q(constituency__icontains=search_query) |
            Q(election_symbol__icontains=search_query) |
            Q(election_number__icontains=search_query)
        )
    
    # Add average rating for each candidate
    for candidate in candidates_queryset:
        avg_rating = candidate.ratings.aggregate(avg_stars=Avg('stars'))['avg_stars']
        candidate.avg_rating = round(avg_rating, 1) if avg_rating else 0
    
    # Pagination
    paginator = Paginator(candidates_queryset, 20)  # 20 candidates per page
    page_number = request.GET.get('page')
    candidates = paginator.get_page(page_number)
    
    context = {
        'page_title': f'مرشحو محافظة {governorate.name}',
        'governorate': governorate,
        'candidates': candidates,
        'search_query': search_query,
        'meta_description': f'قائمة جميع مرشحي محافظة {governorate.name} - تعرف على مرشحيك وتقييماتهم',
    }
    return render(request, 'naebak/governorate_candidates_list.html', context)


def create_governorates_data(request):
    """
    View to create initial governorate data (for development purposes)
    This should be removed in production or protected with admin permissions
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('naebak:home')
    
    # List of Egyptian governorates
    governorates_data = [
        {'name': 'القاهرة', 'slug': 'cairo'},
        {'name': 'الجيزة', 'slug': 'giza'},
        {'name': 'الإسكندرية', 'slug': 'alexandria'},
        {'name': 'القليوبية', 'slug': 'qalyubia'},
        {'name': 'الشرقية', 'slug': 'sharqia'},
        {'name': 'المنوفية', 'slug': 'monufia'},
        {'name': 'الغربية', 'slug': 'gharbia'},
        {'name': 'الدقهلية', 'slug': 'dakahlia'},
        {'name': 'كفر الشيخ', 'slug': 'kafr-el-sheikh'},
        {'name': 'دمياط', 'slug': 'damietta'},
        {'name': 'البحيرة', 'slug': 'beheira'},
        {'name': 'الإسماعيلية', 'slug': 'ismailia'},
        {'name': 'بورسعيد', 'slug': 'port-said'},
        {'name': 'السويس', 'slug': 'suez'},
        {'name': 'شمال سيناء', 'slug': 'north-sinai'},
        {'name': 'جنوب سيناء', 'slug': 'south-sinai'},
        {'name': 'الفيوم', 'slug': 'fayoum'},
        {'name': 'بني سويف', 'slug': 'beni-suef'},
        {'name': 'المنيا', 'slug': 'minya'},
        {'name': 'أسيوط', 'slug': 'asyut'},
        {'name': 'سوهاج', 'slug': 'sohag'},
        {'name': 'قنا', 'slug': 'qena'},
        {'name': 'الأقصر', 'slug': 'luxor'},
        {'name': 'أسوان', 'slug': 'aswan'},
        {'name': 'البحر الأحمر', 'slug': 'red-sea'},
        {'name': 'الوادي الجديد', 'slug': 'new-valley'},
        {'name': 'مطروح', 'slug': 'matrouh'},
    ]
    
    created_count = 0
    for gov_data in governorates_data:
        governorate, created = Governorate.objects.get_or_create(
            slug=gov_data['slug'],
            defaults={'name': gov_data['name']}
        )
        if created:
            created_count += 1
    
    messages.success(request, f'تم إنشاء {created_count} محافظة جديدة.')
    return redirect('naebak:admin_panel')




@login_required
def user_management(request):
    """
    صفحة إدارة المستخدمين للأدمن الرئيسي
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('naebak:home')

    users = User.objects.all().order_by('username')

    # Filtering
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        users = users.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query))

    if role_filter:
        if role_filter == 'citizen':
            users = users.filter(is_superuser=False, candidate_profile__isnull=True)
        elif role_filter == 'candidate':
            users = users.filter(candidate_profile__isnull=False)
        elif role_filter == 'admin':
            users = users.filter(is_superuser=True)

    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'إدارة المستخدمين',
        'users': page_obj,
    }
    return render(request, 'naebak/user_management.html', context)




import json
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import InMemoryUploadedFile
import tempfile
import os
from datetime import datetime


@staff_member_required
@require_http_methods(["GET"])
def backup_data(request):
    """
    إنشاء نسخة احتياطية من البيانات وتحميلها كملف JSON
    """
    try:
        # Get all models data
        from .models import Governorate, Candidate, ElectoralPromise, PublicServiceHistory, Message, Rating
        
        backup_data = {}
        
        # Backup Governorates
        governorates = Governorate.objects.all()
        backup_data['governorates'] = json.loads(serializers.serialize('json', governorates))
        
        # Backup Candidates
        candidates = Candidate.objects.all()
        backup_data['candidates'] = json.loads(serializers.serialize('json', candidates))
        
        # Backup Electoral Promises
        promises = ElectoralPromise.objects.all()
        backup_data['electoral_promises'] = json.loads(serializers.serialize('json', promises))
        
        # Backup Public Service History
        service_history = PublicServiceHistory.objects.all()
        backup_data['service_history'] = json.loads(serializers.serialize('json', service_history))
        
        # Backup Messages
        messages_data = Message.objects.all()
        backup_data['messages'] = json.loads(serializers.serialize('json', messages_data))
        
        # Backup Ratings if exists
        try:
            ratings = Rating.objects.all()
            backup_data['ratings'] = json.loads(serializers.serialize('json', ratings))
        except:
            backup_data['ratings'] = []
        
        # Backup Users (excluding passwords for security)
        users = User.objects.all()
        users_data = []
        for user in users:
            user_data = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat(),
            }
            users_data.append(user_data)
        backup_data['users'] = users_data
        
        # Add metadata
        backup_data['metadata'] = {
            'backup_date': datetime.now().isoformat(),
            'version': '1.0',
            'description': 'Naebak Project Database Backup'
        }
        
        # Create response with JSON data
        response = HttpResponse(
            json.dumps(backup_data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8'
        )
        
        # Set filename with current date
        filename = f"naebak_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}'
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def restore_data(request):
    """
    استعادة البيانات من ملف JSON
    """
    try:
        if 'backup_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'لم يتم رفع أي ملف'
            }, status=400)
        
        backup_file = request.FILES['backup_file']
        
        # Validate file type
        if not backup_file.name.endswith('.json'):
            return JsonResponse({
                'success': False,
                'error': 'يجب أن يكون الملف من نوع JSON'
            }, status=400)
        
        # Read and parse JSON data
        try:
            file_content = backup_file.read().decode('utf-8')
            backup_data = json.loads(file_content)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'الملف غير صالح أو تالف'
            }, status=400)
        
        # Validate backup structure
        required_keys = ['governorates', 'candidates', 'users', 'metadata']
        if not all(key in backup_data for key in required_keys):
            return JsonResponse({
                'success': False,
                'error': 'هيكل الملف غير صحيح'
            }, status=400)
        
        from .models import Governorate, Candidate, ElectoralPromise, PublicServiceHistory, Message
        
        # Clear existing data (optional - can be made configurable)
        clear_existing = request.POST.get('clear_existing', 'false').lower() == 'true'
        
        if clear_existing:
            # Clear in reverse order to avoid foreign key constraints
            Message.objects.all().delete()
            PublicServiceHistory.objects.all().delete()
            ElectoralPromise.objects.all().delete()
            Candidate.objects.all().delete()
            Governorate.objects.all().delete()
        
        # Restore Governorates
        for gov_data in backup_data['governorates']:
            fields = gov_data['fields']
            Governorate.objects.get_or_create(
                id=gov_data['pk'],
                defaults={
                    'name': fields['name'],
                    'slug': fields['slug'],
                    'description': fields.get('description', ''),
                }
            )
        
        # Restore Candidates
        for candidate_data in backup_data['candidates']:
            fields = candidate_data['fields']
            try:
                user = User.objects.get(id=fields['user'])
                governorate = None
                if fields.get('governorate'):
                    governorate = Governorate.objects.get(id=fields['governorate'])
                
                Candidate.objects.get_or_create(
                    id=candidate_data['pk'],
                    defaults={
                        'user': user,
                        'name': fields['name'],
                        'role': fields.get('role', 'مرشح مجلس النواب'),
                        'governorate': governorate,
                        'constituency': fields.get('constituency', ''),
                        'bio': fields.get('bio', ''),
                        'is_featured': fields.get('is_featured', False),
                        'election_symbol': fields.get('election_symbol', ''),
                        'election_number': fields.get('election_number', ''),
                    }
                )
            except User.DoesNotExist:
                continue  # Skip if user doesn't exist
        
        # Restore Electoral Promises
        if 'electoral_promises' in backup_data:
            for promise_data in backup_data['electoral_promises']:
                fields = promise_data['fields']
                try:
                    candidate = Candidate.objects.get(id=fields['candidate'])
                    ElectoralPromise.objects.get_or_create(
                        id=promise_data['pk'],
                        defaults={
                            'candidate': candidate,
                            'title': fields['title'],
                            'description': fields['description'],
                            'order': fields.get('order', 0),
                        }
                    )
                except Candidate.DoesNotExist:
                    continue
        
        # Restore Service History
        if 'service_history' in backup_data:
            for history_data in backup_data['service_history']:
                fields = history_data['fields']
                try:
                    candidate = Candidate.objects.get(id=fields['candidate'])
                    PublicServiceHistory.objects.get_or_create(
                        id=history_data['pk'],
                        defaults={
                            'candidate': candidate,
                            'start_year': fields['start_year'],
                            'end_year': fields['end_year'],
                            'position': fields['position'],
                            'description': fields['description'],
                        }
                    )
                except Candidate.DoesNotExist:
                    continue
        
        return JsonResponse({
            'success': True,
            'message': 'تم استعادة البيانات بنجاح'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'حدث خطأ أثناء استعادة البيانات: {str(e)}'
        }, status=500)




@require_http_methods(["GET", "POST"])
def send_message_to_candidate(request, candidate_id):
    """
    صفحة إرسال رسالة إلى مرشح
    """
    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        messages.error(request, 'المرشح غير موجود.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        # Get form data
        subject = request.POST.get('subject', '').strip()
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment')
        
        # Validation
        if not subject:
            messages.error(request, 'يرجى إدخال موضوع الرسالة.')
        elif not content:
            messages.error(request, 'يرجى إدخال محتوى الرسالة.')
        elif len(subject) > 300:
            messages.error(request, 'موضوع الرسالة طويل جداً (الحد الأقصى 300 حرف).')
        elif len(content) > 5000:
            messages.error(request, 'محتوى الرسالة طويل جداً (الحد الأقصى 5000 حرف).')
        else:
            try:
                # Create message
                message = Message.objects.create(
                    candidate=candidate,
                    subject=subject,
                    content=content,
                    attachment=attachment
                )
                
                # Set sender information
                if request.user.is_authenticated:
                    message.sender_user = request.user
                    message.sender_name = request.user.get_full_name() or request.user.username
                    message.sender_email = request.user.email
                else:
                    # For anonymous users
                    sender_name = request.POST.get('sender_name', '').strip()
                    sender_email = request.POST.get('sender_email', '').strip()
                    
                    if not sender_name:
                        messages.error(request, 'يرجى إدخال اسمك.')
                        return render(request, 'naebak/send_message.html', {
                            'candidate': candidate,
                            'page_title': f'إرسال رسالة إلى {candidate.name}'
                        })
                    
                    if not sender_email:
                        messages.error(request, 'يرجى إدخال بريدك الإلكتروني.')
                        return render(request, 'naebak/send_message.html', {
                            'candidate': candidate,
                            'page_title': f'إرسال رسالة إلى {candidate.name}'
                        })
                    
                    # Validate email format
                    from django.core.validators import validate_email
                    from django.core.exceptions import ValidationError
                    try:
                        validate_email(sender_email)
                    except ValidationError:
                        messages.error(request, 'يرجى إدخال بريد إلكتروني صحيح.')
                        return render(request, 'naebak/send_message.html', {
                            'candidate': candidate,
                            'page_title': f'إرسال رسالة إلى {candidate.name}'
                        })
                    
                    message.sender_name = sender_name
                    message.sender_email = sender_email
                
                message.save()
                
                messages.success(request, f'تم إرسال رسالتك إلى {candidate.name} بنجاح!')
                return redirect('naebak:candidate_detail', pk=candidate.id)
                
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إرسال الرسالة: {str(e)}')
    
    context = {
        'candidate': candidate,
        'page_title': f'إرسال رسالة إلى {candidate.name}',
    }
    return render(request, 'naebak/send_message.html', context)


@login_required
def my_messages(request):
    """
    صفحة رسائل المواطن المرسلة والمستلمة
    """
    # Get filter parameters
    message_type = request.GET.get('type', 'all')  # all, sent, received
    search_query = request.GET.get('search', '')
    
    # Get messages sent by this user (original messages only, not replies)
    sent_messages = Message.objects.filter(
        sender_user=request.user,
        reply_to__isnull=True
    ).select_related('candidate')
    
    # Get messages received by this user (replies to their messages)
    received_messages = Message.objects.filter(
        reply_to__sender_user=request.user
    ).select_related('candidate', 'reply_to')
    
    # Combine and filter based on type
    if message_type == 'sent':
        messages_queryset = sent_messages
    elif message_type == 'received':
        messages_queryset = received_messages
    else:  # all
        # Combine sent and received messages
        from django.db.models import Q
        messages_queryset = Message.objects.filter(
            Q(sender_user=request.user, reply_to__isnull=True) |  # Sent messages
            Q(reply_to__sender_user=request.user)  # Received messages (replies)
        ).select_related('candidate', 'reply_to')
    
    # Apply search filter
    if search_query:
        messages_queryset = messages_queryset.filter(
            Q(subject__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(candidate__name__icontains=search_query)
        )
    
    # Order by timestamp (newest first)
    messages_queryset = messages_queryset.order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(messages_queryset, 15)  # Show 15 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_sent = sent_messages.count()
    total_received = received_messages.count()
    unread_received = received_messages.filter(is_read=False).count()
    
    context = {
        'page_title': 'إدارة الرسائل',
        'messages': page_obj,
        'message_type': message_type,
        'search_query': search_query,
        'total_sent': total_sent,
        'total_received': total_received,
        'unread_received': unread_received,
    }
    return render(request, 'naebak/my_messages.html', context)


@login_required
def message_thread(request, message_id):
    """
    صفحة عرض سلسلة الرسائل والردود مع إمكانية الرد
    """
    try:
        # Get the original message - can be sent by user or received by user
        original_message = Message.objects.select_related('candidate', 'sender_user').get(
            Q(id=message_id, sender_user=request.user, reply_to__isnull=True) |  # User's original message
            Q(id=message_id, reply_to__sender_user=request.user)  # Reply to user's message
        )
    except Message.DoesNotExist:
        messages.error(request, 'الرسالة غير موجودة أو ليس لديك صلاحية لعرضها.')
        return redirect('naebak:my_messages')
    
    # If this is a reply, get the original message
    if original_message.reply_to:
        root_message = original_message.reply_to
    else:
        root_message = original_message
    
    # Mark received messages as read
    if original_message.reply_to and original_message.reply_to.sender_user == request.user:
        if not original_message.is_read:
            original_message.is_read = True
            original_message.save()
    
    # Handle reply submission
    if request.method == 'POST':
        reply_content = request.POST.get('reply_content')
        if reply_content and reply_content.strip():
            # Create reply message
            Message.objects.create(
                candidate=root_message.candidate,
                sender_user=request.user,
                sender_name=request.user.get_full_name() or request.user.username,
                sender_email=request.user.email,
                subject=f"رد: {root_message.subject}",
                content=reply_content.strip(),
                reply_to=root_message,
                is_read=False  # Will be read by candidate
            )
            messages.success(request, 'تم إرسال الرد بنجاح.')
            return redirect('naebak:message_thread', message_id=root_message.id)
        else:
            messages.error(request, 'يرجى كتابة محتوى الرد.')
    
    # Get all messages in this conversation thread
    conversation_messages = Message.objects.filter(
        Q(id=root_message.id) |  # Original message
        Q(reply_to=root_message)  # All replies
    ).select_related('candidate', 'sender_user').order_by('timestamp')
    
    # Check if user can reply (only if they sent the original message)
    can_reply = root_message.sender_user == request.user
    
    context = {
        'page_title': f'محادثة - {root_message.subject}',
        'root_message': root_message,
        'conversation_messages': conversation_messages,
        'can_reply': can_reply,
    }
    return render(request, 'naebak/message_thread.html', context)



# ===== NOTIFICATION API VIEWS =====

@login_required
@require_GET
def get_notifications(request):
    """API endpoint to get user notifications (unread messages and ratings)"""
    try:
        user = request.user
        notifications = []
        
        # Get unread messages sent to user (if user is a candidate)
        if hasattr(user, 'candidate_profile'):
            candidate = user.candidate_profile
            unread_messages = Message.objects.filter(
                candidate=candidate,
                is_read=False
            ).select_related('sender_user').order_by('-timestamp')[:10]
            
            for message in unread_messages:
                sender_name = message.sender_user.get_full_name() if message.sender_user else message.sender_name
                notifications.append({
                    'id': message.id,
                    'type': 'message',
                    'title': f'رسالة جديدة من {sender_name}',
                    'content': message.subject,
                    'timestamp': message.timestamp.isoformat(),
                    'url': f'/message-thread/{message.id}/',
                    'avatar': '/static/naebak/images/default-avatar.png'
                })
        
        # Get unread messages received by user (replies to their messages)
        unread_replies = Message.objects.filter(
            reply_to__sender_user=user,
            is_read=False
        ).exclude(sender_user=user).select_related('candidate', 'sender_user').order_by('-timestamp')[:10]
        
        for reply in unread_replies:
            sender_name = reply.sender_user.get_full_name() if reply.sender_user else reply.sender_name
            notifications.append({
                'id': reply.id,
                'type': 'reply',
                'title': f'رد جديد من {sender_name}',
                'content': reply.subject,
                'timestamp': reply.timestamp.isoformat(),
                'url': f'/message-thread/{reply.reply_to.id}/',
                'avatar': '/static/naebak/images/default-avatar.png'
            })
        
        # Get unread ratings (if user is a candidate)
        if hasattr(user, 'candidate_profile'):
            candidate = user.candidate_profile
            unread_ratings = Rating.objects.filter(
                candidate=candidate,
                is_read=False
            ).select_related('citizen').order_by('-timestamp')[:10]
            
            for rating in unread_ratings:
                citizen_name = rating.citizen.get_full_name() or rating.citizen.username
                stars_text = '⭐' * rating.stars
                notifications.append({
                    'id': rating.id,
                    'type': 'rating',
                    'title': f'تقييم جديد من {citizen_name}',
                    'content': f'{stars_text} - {rating.comment[:50]}...' if rating.comment else f'{stars_text}',
                    'timestamp': rating.timestamp.isoformat(),
                    'url': f'/candidate/{candidate.id}/#ratings',
                    'avatar': '/static/naebak/images/default-avatar.png'
                })
        
        # Sort all notifications by timestamp (newest first)
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Get total unread count
        unread_count = len(notifications)
        
        return JsonResponse({
            'success': True,
            'notifications': notifications[:10],  # Limit to 10 most recent
            'unread_count': unread_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def mark_notification_read(request):
    """API endpoint to mark a notification as read"""
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        notification_type = data.get('notification_type')
        
        if not notification_id or not notification_type:
            return JsonResponse({
                'success': False,
                'error': 'Missing notification_id or notification_type'
            }, status=400)
        
        if notification_type == 'message':
            message = get_object_or_404(Message, id=notification_id)
            # Check if user has permission to mark as read
            if (hasattr(request.user, 'candidate_profile') and 
                message.candidate == request.user.candidate_profile):
                message.is_read = True
                message.save()
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                }, status=403)
                
        elif notification_type == 'reply':
            reply = get_object_or_404(Message, id=notification_id)
            # Check if user is the recipient of the reply
            if reply.reply_to and reply.reply_to.sender_user == request.user:
                reply.is_read = True
                reply.save()
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                }, status=403)
                
        elif notification_type == 'rating':
            rating = get_object_or_404(Rating, id=notification_id)
            # Check if user is the candidate being rated
            if (hasattr(request.user, 'candidate_profile') and 
                rating.candidate == request.user.candidate_profile):
                rating.is_read = True
                rating.save()
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied'
                }, status=403)
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """API endpoint to mark all notifications as read"""
    try:
        user = request.user
        
        # Mark all unread messages as read (if user is a candidate)
        if hasattr(user, 'candidate_profile'):
            candidate = user.candidate_profile
            Message.objects.filter(
                candidate=candidate,
                is_read=False
            ).update(is_read=True)
            
            Rating.objects.filter(
                candidate=candidate,
                is_read=False
            ).update(is_read=True)
        
        # Mark all unread replies as read
        Message.objects.filter(
            reply_to__sender_user=user,
            is_read=False
        ).exclude(sender_user=user).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'message': 'All notifications marked as read'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



# ===== CANDIDATE CREATION VIEWS =====

@login_required
def create_candidate(request):
    """
    إنشاء حساب مرشح جديد
    """
    # التحقق من صلاحيات الأدمن
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            candidate_name = request.POST.get('candidate_name', '').strip()
            role = request.POST.get('role', 'مرشح مجلس النواب').strip()
            governorate_id = request.POST.get('governorate')
            constituency = request.POST.get('constituency', '').strip()
            bio = request.POST.get('bio', '').strip()
            election_symbol = request.POST.get('election_symbol', '').strip()
            election_number = request.POST.get('election_number', '').strip()
            
            # Validation
            if not all([username, email, password, candidate_name]):
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة')
                return render(request, 'naebak/create_candidate.html', {
                    'page_title': 'إنشاء حساب مرشح جديد',
                    'governorates': Governorate.objects.all().order_by('name')
                })
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'اسم المستخدم موجود بالفعل')
                return render(request, 'naebak/create_candidate.html', {
                    'page_title': 'إنشاء حساب مرشح جديد',
                    'governorates': Governorate.objects.all().order_by('name')
                })
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'البريد الإلكتروني موجود بالفعل')
                return render(request, 'naebak/create_candidate.html', {
                    'page_title': 'إنشاء حساب مرشح جديد',
                    'governorates': Governorate.objects.all().order_by('name')
                })
            
            # Get governorate
            governorate = None
            if governorate_id:
                try:
                    governorate = Governorate.objects.get(id=governorate_id)
                except Governorate.DoesNotExist:
                    messages.error(request, 'المحافظة المحددة غير موجودة')
                    return render(request, 'naebak/create_candidate.html', {
                        'page_title': 'إنشاء حساب مرشح جديد',
                        'governorates': Governorate.objects.all().order_by('name')
                    })
            
            # Create user account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create candidate profile
            candidate = Candidate.objects.create(
                user=user,
                name=candidate_name,
                role=role,
                governorate=governorate,
                constituency=constituency,
                bio=bio,
                election_symbol=election_symbol,
                election_number=election_number
            )
            
            messages.success(request, f'تم إنشاء حساب المرشح "{candidate_name}" بنجاح')
            return redirect('naebak:admin_panel')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {str(e)}')
            return render(request, 'naebak/create_candidate.html', {
                'page_title': 'إنشاء حساب مرشح جديد',
                'governorates': Governorate.objects.all().order_by('name')
            })
    
    # GET request - show form
    context = {
        'page_title': 'إنشاء حساب مرشح جديد',
        'governorates': Governorate.objects.all().order_by('name')
    }
    return render(request, 'naebak/create_candidate.html', context)


@login_required
def manage_candidates(request):
    """
    إدارة المرشحين - عرض وتعديل وحذف
    """
    # التحقق من صلاحيات الأدمن
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('naebak:home')
    
    # Get all candidates with related data
    candidates_queryset = Candidate.objects.select_related(
        'user', 'governorate'
    ).prefetch_related('ratings', 'messages').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        candidates_queryset = candidates_queryset.filter(
            Q(name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(constituency__icontains=search_query) |
            Q(election_symbol__icontains=search_query) |
            Q(election_number__icontains=search_query)
        )
    
    # Filter by governorate
    governorate_filter = request.GET.get('governorate')
    if governorate_filter:
        candidates_queryset = candidates_queryset.filter(governorate_id=governorate_filter)
    
    # Pagination
    paginator = Paginator(candidates_queryset, 20)  # 20 candidates per page
    page_number = request.GET.get('page')
    candidates = paginator.get_page(page_number)
    
    # Add statistics for each candidate
    for candidate in candidates:
        candidate.total_messages = candidate.messages.count()
        candidate.total_ratings = candidate.ratings.count()
        candidate.avg_rating = candidate.ratings.aggregate(Avg('stars'))['stars__avg'] or 0
        candidate.total_votes = candidate.votes.count()
    
    context = {
        'page_title': 'إدارة المرشحين',
        'candidates': candidates,
        'governorates': Governorate.objects.all().order_by('name'),
        'search_query': search_query,
        'governorate_filter': governorate_filter,
        'total_candidates': candidates_queryset.count(),
    }
    return render(request, 'naebak/manage_candidates.html', context)


@login_required
@require_POST
def delete_candidate(request, candidate_id):
    """
    حذف مرشح
    """
    # التحقق من صلاحيات الأدمن
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'ليس لديك صلاحية لتنفيذ هذا الإجراء'
        }, status=403)
    
    try:
        candidate = get_object_or_404(Candidate, id=candidate_id)
        candidate_name = candidate.name
        user = candidate.user
        
        # Delete candidate (this will also delete the user due to OneToOneField)
        candidate.delete()
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'تم حذف المرشح "{candidate_name}" بنجاح'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'حدث خطأ أثناء حذف المرشح: {str(e)}'
        }, status=500)



# ==================== Candidate Dashboard Views ====================

@login_required
def candidate_dashboard(request):
    """
    لوحة تحكم المرشح الرئيسية
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    # Get candidate statistics
    total_messages = candidate.messages.count()
    unread_messages = candidate.messages.filter(is_read=False).count()
    total_ratings = candidate.ratings.count()
    avg_rating = candidate.ratings.aggregate(Avg('stars'))['stars__avg'] or 0
    total_votes = candidate.votes.count()
    approve_votes = candidate.votes.filter(vote_type='approve').count()
    disapprove_votes = candidate.votes.filter(vote_type='disapprove').count()
    
    # Calculate approval percentage
    approval_percentage = (approve_votes / total_votes * 100) if total_votes > 0 else 0
    
    # Profile completion percentage
    profile_fields = [
        candidate.name, candidate.bio, candidate.electoral_program, 
        candidate.message_to_voters, candidate.profile_picture, 
        candidate.banner_image, candidate.phone_number
    ]
    completed_fields = sum(1 for field in profile_fields if field)
    profile_completion = (completed_fields / len(profile_fields)) * 100
    
    # Recent activity
    recent_messages = candidate.messages.order_by('-timestamp')[:5]
    recent_ratings = candidate.ratings.order_by('-timestamp')[:5]
    
    # Electoral promises count
    promises_count = candidate.electoral_promises.count()
    
    # Social media links status
    social_links_count = sum(1 for link in [
        candidate.youtube_video_url, candidate.facebook_url, 
        candidate.twitter_url, candidate.website_url
    ] if link)
    
    context = {
        'page_title': 'لوحة تحكم المرشح',
        'candidate': candidate,
        'total_messages': total_messages,
        'unread_messages': unread_messages,
        'total_ratings': total_ratings,
        'avg_rating': round(avg_rating, 1),
        'total_votes': total_votes,
        'approve_votes': approve_votes,
        'disapprove_votes': disapprove_votes,
        'approval_percentage': round(approval_percentage, 1),
        'profile_completion': round(profile_completion, 1),
        'promises_count': promises_count,
        'social_links_count': social_links_count,
        'recent_messages': recent_messages,
        'recent_ratings': recent_ratings,
    }
    return render(request, 'naebak/candidate_dashboard.html', context)


@login_required
def candidate_profile_edit(request):
    """
    تعديل الملف الشخصي للمرشح
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        # Update basic information
        candidate.name = request.POST.get('name', candidate.name)
        candidate.role = request.POST.get('role', candidate.role)
        candidate.bio = request.POST.get('bio', candidate.bio)
        candidate.constituency = request.POST.get('constituency', candidate.constituency)
        candidate.election_number = request.POST.get('election_number', candidate.election_number)
        candidate.election_symbol = request.POST.get('election_symbol', candidate.election_symbol)
        candidate.phone_number = request.POST.get('phone_number', candidate.phone_number)
        
        # Update electoral program and messages
        candidate.electoral_program = request.POST.get('electoral_program', candidate.electoral_program)
        candidate.message_to_voters = request.POST.get('message_to_voters', candidate.message_to_voters)
        
        # Update social media and web links
        candidate.youtube_video_url = request.POST.get('youtube_video_url', candidate.youtube_video_url)
        candidate.facebook_url = request.POST.get('facebook_url', candidate.facebook_url)
        candidate.twitter_url = request.POST.get('twitter_url', candidate.twitter_url)
        candidate.website_url = request.POST.get('website_url', candidate.website_url)
        
        # Handle profile image upload
        if 'profile_picture' in request.FILES:
            candidate.profile_picture = request.FILES['profile_picture']
        
        # Handle banner image upload
        if 'banner_image' in request.FILES:
            candidate.banner_image = request.FILES['banner_image']
        
        try:
            candidate.save()
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
            return redirect('naebak:candidate_dashboard')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ البيانات: {str(e)}')
    
    context = {
        'page_title': 'تعديل الملف الشخصي',
        'candidate': candidate,
    }
    return render(request, 'naebak/candidate_profile_edit.html', context)


@login_required
def candidate_electoral_program(request):
    """
    إدارة البرنامج الانتخابي للمرشح
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        # Update electoral program and message to voters
        electoral_program = request.POST.get('electoral_program', '').strip()
        message_to_voters = request.POST.get('message_to_voters', '').strip()
        
        # Validate content length
        if len(electoral_program) > 5000:
            messages.error(request, 'البرنامج الانتخابي يتجاوز الحد المسموح (5000 حرف)')
            return redirect('naebak:candidate_electoral_program')
            
        if len(message_to_voters) > 1000:
            messages.error(request, 'رسالة المنتخبين تتجاوز الحد المسموح (1000 حرف)')
            return redirect('naebak:candidate_electoral_program')
        
        # Update candidate fields
        candidate.electoral_program = electoral_program
        candidate.message_to_voters = message_to_voters
        
        try:
            candidate.save()
            
            # Success message based on what was updated
            updated_items = []
            if electoral_program:
                updated_items.append('البرنامج الانتخابي')
            if message_to_voters:
                updated_items.append('رسالة المنتخبين')
            
            if updated_items:
                message = f'تم تحديث {" و ".join(updated_items)} بنجاح'
            else:
                message = 'تم حفظ التغييرات بنجاح'
                
            messages.success(request, message)
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حفظ البيانات: {str(e)}')
            
        return redirect('naebak:candidate_electoral_program')
    
    context = {
        'page_title': 'البرنامج الانتخابي',
        'candidate': candidate,
    }
    return render(request, 'naebak/candidate_electoral_program.html', context)


@login_required
def candidate_promises(request):
    """
    إدارة الوعود الانتخابية للمرشح
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    promises = candidate.electoral_promises.all().order_by('-created_at')
    
    if request.method == 'POST':
        # Add new promise
        promise_text = request.POST.get('promise_text')
        if promise_text:
            ElectoralPromise.objects.create(
                candidate=candidate,
                promise=promise_text
            )
            messages.success(request, 'تم إضافة الوعد الانتخابي بنجاح')
            return redirect('naebak:candidate_promises')
    
    context = {
        'page_title': 'الوعود الانتخابية',
        'candidate': candidate,
        'promises': promises,
    }
    return render(request, 'naebak/candidate_promises.html', context)


@login_required
def candidate_messages(request):
    """
    إدارة رسائل المرشح
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    # Get messages with pagination
    messages_list = candidate.messages.order_by('-timestamp')
    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    # Mark messages as read when viewed
    candidate.messages.filter(is_read=False).update(is_read=True)
    
    context = {
        'page_title': 'الرسائل الواردة',
        'candidate': candidate,
        'messages': messages_page,
    }
    return render(request, 'naebak/candidate_messages.html', context)


@login_required
def candidate_message_reply(request, message_id):
    """
    الرد على رسالة
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    message = get_object_or_404(Message, id=message_id, candidate=candidate)
    
    if request.method == 'POST':
        reply_text = request.POST.get('reply_text')
        if reply_text:
            # Create reply message
            Message.objects.create(
                candidate=candidate,
                sender_user=request.user,
                sender_name=candidate.name,
                sender_email=candidate.user.email,
                subject=f'رد: {message.subject}',
                content=reply_text,
                parent_message=message,
                is_reply=True
            )
            message.has_reply = True
            message.save()
            messages.success(request, 'تم إرسال الرد بنجاح')
            return redirect('naebak:candidate_messages')
    
    context = {
        'page_title': 'الرد على الرسالة',
        'candidate': candidate,
        'message': message,
    }
    return render(request, 'naebak/candidate_message_reply.html', context)


@login_required
def candidate_ratings_votes(request):
    """
    مراقبة التقييمات والتصويتات
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    # Get ratings with pagination
    ratings_list = candidate.ratings.order_by('-timestamp')
    ratings_paginator = Paginator(ratings_list, 10)
    ratings_page_number = request.GET.get('ratings_page')
    ratings_page = ratings_paginator.get_page(ratings_page_number)
    
    # Get votes with pagination
    votes_list = candidate.votes.order_by('-timestamp')
    votes_paginator = Paginator(votes_list, 10)
    votes_page_number = request.GET.get('votes_page')
    votes_page = votes_paginator.get_page(votes_page_number)
    
    # Calculate statistics
    total_ratings = candidate.ratings.count()
    avg_rating = candidate.ratings.aggregate(Avg('stars'))['stars__avg'] or 0
    total_votes = candidate.votes.count()
    approve_votes = candidate.votes.filter(vote_type='approve').count()
    disapprove_votes = candidate.votes.filter(vote_type='disapprove').count()
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = candidate.ratings.filter(stars=i).count()
    
    context = {
        'page_title': 'التقييمات والتصويتات',
        'candidate': candidate,
        'ratings': ratings_page,
        'votes': votes_page,
        'total_ratings': total_ratings,
        'avg_rating': round(avg_rating, 1),
        'total_votes': total_votes,
        'approve_votes': approve_votes,
        'disapprove_votes': disapprove_votes,
        'rating_distribution': rating_distribution,
    }
    return render(request, 'naebak/candidate_ratings_votes.html', context)


@login_required
@require_POST
def delete_promise(request, promise_id):
    """
    حذف وعد انتخابي
    """
    try:
        candidate = request.user.candidate_profile
        promise = get_object_or_404(ElectoralPromise, id=promise_id, candidate=candidate)
        promise.delete()
        return JsonResponse({'success': True, 'message': 'تم حذف الوعد بنجاح'})
    except Candidate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'غير مصرح لك بهذا الإجراء'}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




# ==========================================
# News Management Views
# ==========================================

@login_required
def news_management(request):
    """
    صفحة إدارة الأخبار - عرض قائمة الأخبار مع إمكانية البحث والتصفية
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    # Base queryset
    news_list = News.objects.all()
    
    # Apply search filter
    if search_query:
        news_list = news_list.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        news_list = news_list.filter(status=status_filter)
    
    # Apply priority filter
    if priority_filter:
        news_list = news_list.filter(priority=priority_filter)
    
    # Order by priority and creation date
    news_list = news_list.order_by('-priority', '-created_at')
    
    # Pagination
    paginator = Paginator(news_list, 10)
    page_number = request.GET.get('page')
    news_page = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_news': News.objects.count(),
        'published_news': News.objects.filter(status='published').count(),
        'draft_news': News.objects.filter(status='draft').count(),
        'archived_news': News.objects.filter(status='archived').count(),
        'urgent_news': News.objects.filter(priority='urgent', status='published').count(),
    }
    
    context = {
        'page_title': 'إدارة الأخبار',
        'news_page': news_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'stats': stats,
        'status_choices': News.STATUS_CHOICES,
        'priority_choices': News.PRIORITY_CHOICES,
    }
    
    return render(request, 'naebak/news_management.html', context)


@login_required
def create_news(request):
    """
    إنشاء خبر جديد
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        try:
            # Create new news item
            news = News.objects.create(
                title=request.POST.get('title'),
                content=request.POST.get('content'),
                status=request.POST.get('status', 'draft'),
                priority=request.POST.get('priority', 'normal'),
                show_on_homepage=request.POST.get('show_on_homepage') == 'on',
                show_on_ticker=request.POST.get('show_on_ticker') == 'on',
                ticker_speed=int(request.POST.get('ticker_speed', 50)),
                meta_description=request.POST.get('meta_description', ''),
                tags=request.POST.get('tags', ''),
                author=request.user
            )
            
            # Handle publish date if provided
            publish_date = request.POST.get('publish_date')
            if publish_date:
                from django.utils.dateparse import parse_datetime
                news.publish_date = parse_datetime(publish_date)
                news.save()
            
            # Handle expire date if provided
            expire_date = request.POST.get('expire_date')
            if expire_date:
                from django.utils.dateparse import parse_datetime
                news.expire_date = parse_datetime(expire_date)
                news.save()
            
            messages.success(request, f'تم إنشاء الخبر "{news.title}" بنجاح.')
            return redirect('naebak:news_management')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إنشاء الخبر: {str(e)}')
    
    context = {
        'page_title': 'إنشاء خبر جديد',
        'status_choices': News.STATUS_CHOICES,
        'priority_choices': News.PRIORITY_CHOICES,
    }
    
    return render(request, 'naebak/create_news.html', context)


@login_required
def edit_news(request, news_id):
    """
    تعديل خبر موجود
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    news = get_object_or_404(News, id=news_id)
    
    if request.method == 'POST':
        try:
            # Update news item
            news.title = request.POST.get('title')
            news.content = request.POST.get('content')
            news.status = request.POST.get('status', 'draft')
            news.priority = request.POST.get('priority', 'normal')
            news.show_on_homepage = request.POST.get('show_on_homepage') == 'on'
            news.show_on_ticker = request.POST.get('show_on_ticker') == 'on'
            news.ticker_speed = int(request.POST.get('ticker_speed', 50))
            news.meta_description = request.POST.get('meta_description', '')
            news.tags = request.POST.get('tags', '')
            
            # Handle publish date if provided
            publish_date = request.POST.get('publish_date')
            if publish_date:
                from django.utils.dateparse import parse_datetime
                news.publish_date = parse_datetime(publish_date)
            
            # Handle expire date if provided
            expire_date = request.POST.get('expire_date')
            if expire_date:
                from django.utils.dateparse import parse_datetime
                news.expire_date = parse_datetime(expire_date)
            else:
                news.expire_date = None
            
            news.save()
            
            messages.success(request, f'تم تحديث الخبر "{news.title}" بنجاح.')
            return redirect('naebak:news_management')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء تحديث الخبر: {str(e)}')
    
    context = {
        'page_title': f'تعديل الخبر: {news.title}',
        'news': news,
        'status_choices': News.STATUS_CHOICES,
        'priority_choices': News.PRIORITY_CHOICES,
    }
    
    return render(request, 'naebak/edit_news.html', context)


@login_required
def delete_news(request, news_id):
    """
    حذف خبر
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    news = get_object_or_404(News, id=news_id)
    
    if request.method == 'POST':
        news_title = news.title
        news.delete()
        messages.success(request, f'تم حذف الخبر "{news_title}" بنجاح.')
        return redirect('naebak:news_management')
    
    context = {
        'page_title': f'حذف الخبر: {news.title}',
        'news': news,
    }
    
    return render(request, 'naebak/delete_news.html', context)


@login_required
def toggle_news_status(request, news_id):
    """
    تغيير حالة الخبر (نشر/إيقاف)
    """
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'ليس لديك صلاحية لهذا الإجراء.'})
    
    news = get_object_or_404(News, id=news_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['draft', 'published', 'archived']:
            news.status = new_status
            news.save()
            
            return JsonResponse({
                'success': True,
                'message': f'تم تغيير حالة الخبر إلى "{news.get_status_display()}"',
                'new_status': new_status,
                'status_display': news.get_status_display()
            })
    
    return JsonResponse({'success': False, 'message': 'حدث خطأ أثناء تغيير حالة الخبر.'})


def get_ticker_news(request):
    """
    API endpoint to get news for ticker display
    """
    ticker_news = News.get_ticker_news()
    
    news_data = []
    for news in ticker_news:
        news_data.append({
            'id': news.id,
            'title': news.title,
            'content': news.content,
            'priority': news.priority,
            'priority_class': news.get_priority_class(),
            'ticker_speed': news.ticker_speed,
        })
    
    return JsonResponse({
        'success': True,
        'news': news_data,
        'count': len(news_data)
    })


def news_detail(request, news_id):
    """
    عرض تفاصيل خبر معين
    """
    news = get_object_or_404(News, id=news_id)
    
    # Check if news is published and not expired
    if not news.is_published() and not request.user.is_superuser:
        messages.error(request, 'هذا الخبر غير متاح للعرض.')
        return redirect('naebak:home')
    
    # Increment views count
    news.increment_views()
    
    # Get related news (same priority or tags)
    related_news = News.get_active_news().exclude(id=news.id)
    if news.tags:
        # Try to find news with similar tags
        tags_list = [tag.strip() for tag in news.tags.split(',')]
        for tag in tags_list:
            related_news = related_news.filter(tags__icontains=tag)
            break
    
    related_news = related_news[:5]
    
    context = {
        'page_title': news.title,
        'news': news,
        'related_news': related_news,
        'meta_description': news.meta_description or news.content[:160],
    }
    
    return render(request, 'naebak/news_detail.html', context)



# ==========================================
# Activity Monitoring Views
# ==========================================

@login_required
def activity_monitoring(request):
    """
    صفحة مراقبة النشاط - عرض سجلات الأنشطة والإحصائيات
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    # Get filter parameters
    action_filter = request.GET.get('action', '')
    severity_filter = request.GET.get('severity', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    activities = ActivityLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply filters
    if action_filter:
        activities = activities.filter(action_type=action_filter)
    
    if severity_filter:
        activities = activities.filter(severity=severity_filter)
    
    if user_filter:
        activities = activities.filter(user_id=user_filter)
    
    if date_from:
        from django.utils.dateparse import parse_date
        date_from_parsed = parse_date(date_from)
        if date_from_parsed:
            activities = activities.filter(timestamp__date__gte=date_from_parsed)
    
    if date_to:
        from django.utils.dateparse import parse_date
        date_to_parsed = parse_date(date_to)
        if date_to_parsed:
            activities = activities.filter(timestamp__date__lte=date_to_parsed)
    
    if search_query:
        activities = activities.filter(
            Q(description__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    activities_page = paginator.get_page(page_number)
    
    # Get statistics
    stats = ActivityLog.get_activity_stats(days=30)
    
    # Get recent security alerts
    security_alerts = ActivityLog.get_security_alerts(days=7)[:10]
    
    # Get unique users for filter dropdown
    active_users = User.objects.filter(
        activitylog__timestamp__gte=timezone.now() - timezone.timedelta(days=30)
    ).distinct().order_by('first_name', 'last_name')
    
    context = {
        'page_title': 'مراقبة النشاط',
        'activities_page': activities_page,
        'stats': stats,
        'security_alerts': security_alerts,
        'active_users': active_users,
        'action_choices': ActivityLog.ACTION_TYPES,
        'severity_choices': ActivityLog.SEVERITY_LEVELS,
        'filters': {
            'action': action_filter,
            'severity': severity_filter,
            'user': user_filter,
            'date_from': date_from,
            'date_to': date_to,
            'search': search_query,
        }
    }
    
    return render(request, 'naebak/activity_monitoring.html', context)


@login_required
def activity_detail(request, activity_id):
    """
    عرض تفاصيل نشاط معين
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    activity = get_object_or_404(ActivityLog, id=activity_id)
    
    context = {
        'page_title': f'تفاصيل النشاط: {activity.get_action_type_display()}',
        'activity': activity,
    }
    
    return render(request, 'naebak/activity_detail.html', context)


@login_required
def user_activity_history(request, user_id):
    """
    عرض سجل أنشطة مستخدم معين
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    user = get_object_or_404(User, id=user_id)
    activities = ActivityLog.get_activities_by_user(user, limit=50)
    
    # Pagination
    paginator = Paginator(activities, 15)
    page_number = request.GET.get('page')
    activities_page = paginator.get_page(page_number)
    
    context = {
        'page_title': f'سجل أنشطة: {user.get_full_name()}',
        'target_user': user,
        'activities_page': activities_page,
    }
    
    return render(request, 'naebak/user_activity_history.html', context)


def get_activity_stats_api(request):
    """
    API endpoint للحصول على إحصائيات النشاط
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'غير مصرح'}, status=403)
    
    days = int(request.GET.get('days', 7))
    stats = ActivityLog.get_activity_stats(days=days)
    
    # Format data for charts
    chart_data = {
        'activity_breakdown': [
            {'name': dict(ActivityLog.ACTION_TYPES).get(item['action_type'], item['action_type']), 
             'value': item['count']}
            for item in stats['activity_breakdown']
        ],
        'daily_activities': []  # This would need additional query for daily breakdown
    }
    
    return JsonResponse({
        'success': True,
        'stats': stats,
        'chart_data': chart_data
    })


# Helper function to log activities (to be used throughout the application)
def log_user_activity(user, action_type, description, request=None, related_object=None, severity='info', extra_data=None):
    """
    دالة مساعدة لتسجيل أنشطة المستخدمين
    """
    try:
        ActivityLog.log_activity(
            user=user,
            action_type=action_type,
            description=description,
            severity=severity,
            request=request,
            related_object=related_object,
            extra_data=extra_data
        )
    except Exception as e:
        # Log the error but don't break the main functionality
        print(f"Error logging activity: {str(e)}")


# Middleware-like function to automatically log certain activities
def auto_log_activity(view_func):
    """
    Decorator to automatically log certain activities
    """
    def wrapper(request, *args, **kwargs):
        # Execute the original view
        response = view_func(request, *args, **kwargs)
        
        # Log activity based on view name and method
        if request.user.is_authenticated:
            view_name = view_func.__name__
            
            # Define activity mappings
            activity_mappings = {
                'user_login': ('login', 'تسجيل دخول المستخدم'),
                'user_logout': ('logout', 'تسجيل خروج المستخدم'),
                'citizen_register': ('register', 'تسجيل حساب مواطن جديد'),
                'create_candidate': ('candidate_created', 'إنشاء حساب مرشح جديد'),
                'create_news': ('news_created', 'إنشاء خبر جديد'),
                'send_message_to_candidate': ('message_sent', 'إرسال رسالة لمرشح'),
            }
            
            if view_name in activity_mappings and request.method == 'POST':
                action_type, description = activity_mappings[view_name]
                log_user_activity(
                    user=request.user,
                    action_type=action_type,
                    description=f"{description} - {request.user.get_full_name()}",
                    request=request
                )
        
        return response
    
    return wrapper


# ==========================================
# Reports and Statistics Views
# ==========================================

@login_required
def reports_dashboard(request):
    """
    لوحة التقارير والإحصائيات الرئيسية
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    from datetime import timedelta
    from django.db.models import Count, Avg, Sum, Q, F
    from django.db.models.functions import TruncDate, TruncMonth
    
    # Date range for analysis (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # === GENERAL STATISTICS ===
    general_stats = {
        'total_users': User.objects.count(),
        'total_candidates': Candidate.objects.count(),
        'total_governorates': Governorate.objects.count(),
        'total_messages': Message.objects.count(),
        'total_ratings': Rating.objects.count(),
        'total_votes': Vote.objects.count(),
        'total_promises': ElectoralPromise.objects.count(),
        'total_news': News.objects.count(),
        'active_users': User.objects.filter(last_login__gte=start_date).count(),
        'published_news': News.objects.filter(status='published').count(),
    }
    
    # === USER ENGAGEMENT STATISTICS ===
    engagement_stats = {
        'new_users_period': User.objects.filter(date_joined__gte=start_date).count(),
        'active_users_period': User.objects.filter(last_login__gte=start_date).count(),
        'messages_period': Message.objects.filter(timestamp__gte=start_date).count(),
        'ratings_period': Rating.objects.filter(timestamp__gte=start_date).count(),
        'votes_period': Vote.objects.filter(timestamp__gte=start_date).count(),
    }
    
    # === CANDIDATE PERFORMANCE ===
    candidate_stats = []
    candidates = Candidate.objects.annotate(
        total_messages=Count('messages'),
        total_ratings=Count('ratings'),
        avg_rating=Avg('ratings__stars'),
        total_votes=Count('votes'),
        approve_votes=Count('votes', filter=Q(votes__vote_type='approve')),
        disapprove_votes=Count('votes', filter=Q(votes__vote_type='disapprove'))
    ).order_by('-total_messages')[:10]
    
    for candidate in candidates:
        approval_rate = 0
        if candidate.total_votes > 0:
            approval_rate = (candidate.approve_votes / candidate.total_votes) * 100
        
        candidate_stats.append({
            'candidate': candidate,
            'total_messages': candidate.total_messages,
            'total_ratings': candidate.total_ratings,
            'avg_rating': round(candidate.avg_rating or 0, 1),
            'total_votes': candidate.total_votes,
            'approval_rate': round(approval_rate, 1),
            'engagement_score': candidate.total_messages + candidate.total_ratings + candidate.total_votes
        })
    
    # === GOVERNORATE STATISTICS ===
    governorate_stats = []
    governorates = Governorate.objects.annotate(
        candidate_count=Count('candidates'),
        total_messages=Count('candidates__messages'),
        total_ratings=Count('candidates__ratings'),
        total_votes=Count('candidates__votes')
    ).order_by('-candidate_count')
    
    for gov in governorates:
        governorate_stats.append({
            'governorate': gov,
            'candidate_count': gov.candidate_count,
            'total_messages': gov.total_messages,
            'total_ratings': gov.total_ratings,
            'total_votes': gov.total_votes,
            'activity_score': gov.total_messages + gov.total_ratings + gov.total_votes
        })
    
    # === DAILY ACTIVITY TRENDS ===
    daily_activities = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        daily_data = {
            'date': date.strftime('%Y-%m-%d'),
            'users': User.objects.filter(last_login__date=date.date()).count(),
            'messages': Message.objects.filter(timestamp__date=date.date()).count(),
            'ratings': Rating.objects.filter(timestamp__date=date.date()).count(),
            'votes': Vote.objects.filter(timestamp__date=date.date()).count(),
        }
        daily_activities.append(daily_data)
    
    # === TOP PERFORMING CONTENT ===
    top_news = News.objects.filter(
        status='published',
        publish_date__gte=start_date
    ).order_by('-views_count')[:5]
    
    top_promises = ElectoralPromise.objects.annotate(
        rating_count=Count('candidate__ratings')
    ).order_by('-rating_count')[:5]
    
    # === SYSTEM HEALTH METRICS ===
    system_health = {
        'error_count': ActivityLog.objects.filter(
            severity__in=['error', 'critical'],
            timestamp__gte=start_date
        ).count(),
        'warning_count': ActivityLog.objects.filter(
            severity='warning',
            timestamp__gte=start_date
        ).count(),
        'login_success_rate': 0,  # Would need more detailed logging
        'avg_response_time': 0,   # Would need performance monitoring
    }
    
    # Calculate login success rate if we have the data
    total_login_attempts = ActivityLog.objects.filter(
        action_type='login',
        timestamp__gte=start_date
    ).count()
    
    if total_login_attempts > 0:
        successful_logins = ActivityLog.objects.filter(
            action_type='login',
            severity='info',
            timestamp__gte=start_date
        ).count()
        system_health['login_success_rate'] = round((successful_logins / total_login_attempts) * 100, 1)
    
    context = {
        'page_title': 'التقارير والإحصائيات',
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        'general_stats': general_stats,
        'engagement_stats': engagement_stats,
        'candidate_stats': candidate_stats,
        'governorate_stats': governorate_stats,
        'daily_activities': daily_activities,
        'top_news': top_news,
        'top_promises': top_promises,
        'system_health': system_health,
    }
    
    return render(request, 'naebak/reports_dashboard.html', context)


@login_required
def candidate_performance_report(request):
    """
    تقرير مفصل عن أداء المرشحين
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    from django.db.models import Count, Avg, Q
    
    # Get filter parameters
    governorate_filter = request.GET.get('governorate', '')
    sort_by = request.GET.get('sort', 'engagement')  # engagement, rating, votes
    
    # Base queryset
    candidates = Candidate.objects.annotate(
        total_messages=Count('messages'),
        total_ratings=Count('ratings'),
        avg_rating=Avg('ratings__stars'),
        total_votes=Count('votes'),
        approve_votes=Count('votes', filter=Q(votes__vote_type='approve')),
        disapprove_votes=Count('votes', filter=Q(votes__vote_type='disapprove')),
        total_promises=Count('electoral_promises')
    )
    
    # Apply governorate filter
    if governorate_filter:
        candidates = candidates.filter(governorate_id=governorate_filter)
    
    # Calculate derived metrics
    candidate_data = []
    for candidate in candidates:
        approval_rate = 0
        if candidate.total_votes > 0:
            approval_rate = (candidate.approve_votes / candidate.total_votes) * 100
        
        engagement_score = (
            candidate.total_messages * 3 +  # Messages weighted more
            candidate.total_ratings * 2 +
            candidate.total_votes * 1
        )
        
        candidate_data.append({
            'candidate': candidate,
            'total_messages': candidate.total_messages,
            'total_ratings': candidate.total_ratings,
            'avg_rating': round(candidate.avg_rating or 0, 1),
            'total_votes': candidate.total_votes,
            'approval_rate': round(approval_rate, 1),
            'total_promises': candidate.total_promises,
            'engagement_score': engagement_score,
        })
    
    # Sort candidates
    if sort_by == 'rating':
        candidate_data.sort(key=lambda x: x['avg_rating'], reverse=True)
    elif sort_by == 'votes':
        candidate_data.sort(key=lambda x: x['total_votes'], reverse=True)
    else:  # engagement
        candidate_data.sort(key=lambda x: x['engagement_score'], reverse=True)
    
    # Pagination
    paginator = Paginator(candidate_data, 20)
    page_number = request.GET.get('page')
    candidates_page = paginator.get_page(page_number)
    
    # Get governorates for filter
    governorates = Governorate.objects.all().order_by('name')
    
    context = {
        'page_title': 'تقرير أداء المرشحين',
        'candidates_page': candidates_page,
        'governorates': governorates,
        'current_governorate': governorate_filter,
        'current_sort': sort_by,
    }
    
    return render(request, 'naebak/candidate_performance_report.html', context)


@login_required
def user_engagement_report(request):
    """
    تقرير مفصل عن تفاعل المستخدمين
    """
    if not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    from datetime import timedelta
    from django.db.models import Count, Q
    from django.db.models.functions import TruncDate
    
    # Date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # User engagement metrics
    user_metrics = []
    active_users = User.objects.filter(
        last_login__gte=start_date
    ).annotate(
        messages_sent=Count('message_set', filter=Q(message_set__timestamp__gte=start_date)),
        ratings_given=Count('rating_set', filter=Q(rating_set__timestamp__gte=start_date)),
        votes_cast=Count('vote_set', filter=Q(vote_set__timestamp__gte=start_date))
    ).order_by('-last_login')
    
    for user in active_users:
        engagement_score = (
            user.messages_sent * 3 +
            user.ratings_given * 2 +
            user.votes_cast * 1
        )
        
        user_metrics.append({
            'user': user,
            'messages_sent': user.messages_sent,
            'ratings_given': user.ratings_given,
            'votes_cast': user.votes_cast,
            'engagement_score': engagement_score,
            'last_activity': user.last_login,
        })
    
    # Sort by engagement score
    user_metrics.sort(key=lambda x: x['engagement_score'], reverse=True)
    
    # Daily engagement trends
    daily_engagement = Message.objects.filter(
        timestamp__gte=start_date
    ).extra(
        select={'day': 'date(timestamp)'}
    ).values('day').annotate(
        message_count=Count('id')
    ).order_by('day')
    
    # User registration trends
    registration_trends = User.objects.filter(
        date_joined__gte=start_date
    ).extra(
        select={'day': 'date(date_joined)'}
    ).values('day').annotate(
        user_count=Count('id')
    ).order_by('day')
    
    # Pagination
    paginator = Paginator(user_metrics, 25)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'page_title': 'تقرير تفاعل المستخدمين',
        'users_page': users_page,
        'daily_engagement': list(daily_engagement),
        'registration_trends': list(registration_trends),
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'naebak/user_engagement_report.html', context)


def export_report_csv(request, report_type):
    """
    تصدير التقارير بصيغة CSV
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'غير مصرح'}, status=403)
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    
    # Add BOM for proper UTF-8 encoding in Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    if report_type == 'candidates':
        # Export candidate performance data
        writer.writerow(['اسم المرشح', 'المحافظة', 'الرسائل', 'التقييمات', 'متوسط التقييم', 'التصويتات', 'نسبة التأييد'])
        
        candidates = Candidate.objects.annotate(
            total_messages=Count('messages'),
            total_ratings=Count('ratings'),
            avg_rating=Avg('ratings__stars'),
            total_votes=Count('votes'),
            approve_votes=Count('votes', filter=Q(votes__vote_type='approve'))
        )
        
        for candidate in candidates:
            approval_rate = 0
            if candidate.total_votes > 0:
                approval_rate = (candidate.approve_votes / candidate.total_votes) * 100
            
            writer.writerow([
                candidate.name,
                candidate.governorate.name,
                candidate.total_messages,
                candidate.total_ratings,
                round(candidate.avg_rating or 0, 1),
                candidate.total_votes,
                f"{approval_rate:.1f}%"
            ])
    
    elif report_type == 'engagement':
        # Export user engagement data
        writer.writerow(['اسم المستخدم', 'البريد الإلكتروني', 'الرسائل', 'التقييمات', 'التصويتات', 'آخر نشاط'])
        
        users = User.objects.annotate(
            messages_sent=Count('message_set'),
            ratings_given=Count('rating_set'),
            votes_cast=Count('vote_set')
        ).filter(
            Q(messages_sent__gt=0) | Q(ratings_given__gt=0) | Q(votes_cast__gt=0)
        )
        
        for user in users:
            writer.writerow([
                user.get_full_name(),
                user.email,
                user.messages_sent,
                user.ratings_given,
                user.votes_cast,
                user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'لم يسجل دخول'
            ])
    
    return response


def get_chart_data_api(request):
    """
    API endpoint لبيانات الرسوم البيانية
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'غير مصرح'}, status=403)
    
    chart_type = request.GET.get('type', 'daily_activity')
    days = int(request.GET.get('days', 30))
    
    from datetime import timedelta
    from django.db.models import Count
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    if chart_type == 'daily_activity':
        # Daily activity data
        daily_data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            data = {
                'date': date.strftime('%Y-%m-%d'),
                'messages': Message.objects.filter(timestamp__date=date.date()).count(),
                'ratings': Rating.objects.filter(timestamp__date=date.date()).count(),
                'votes': Vote.objects.filter(timestamp__date=date.date()).count(),
            }
            daily_data.append(data)
        
        return JsonResponse({'data': daily_data})
    
    elif chart_type == 'governorate_distribution':
        # Governorate distribution data
        governorate_data = []
        governorates = Governorate.objects.annotate(
            candidate_count=Count('candidates'),
            activity_count=Count('candidates__messages') + Count('candidates__ratings')
        )
        
        for gov in governorates:
            governorate_data.append({
                'name': gov.name,
                'candidates': gov.candidate_count,
                'activity': gov.activity_count
            })
        
        return JsonResponse({'data': governorate_data})
    
    return JsonResponse({'error': 'نوع الرسم البياني غير مدعوم'}, status=400)



def privacy_policy(request):
    """
    صفحة سياسة الخصوصية
    """
    from datetime import datetime
    context = {
        'page_title': 'سياسة الخصوصية',
        'last_updated': datetime(2025, 1, 15),  # تاريخ آخر تحديث
    }
    return render(request, 'naebak/privacy_policy.html', context)


def terms_of_service(request):
    """
    صفحة شروط الاستخدام
    """
    from datetime import datetime
    context = {
        'page_title': 'شروط الاستخدام',
        'last_updated': datetime(2025, 1, 15),  # تاريخ آخر تحديث
    }
    return render(request, 'naebak/terms_of_service.html', context)

