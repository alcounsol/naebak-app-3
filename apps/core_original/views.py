"""
Views لتطبيق naebak الرئيسي - نسخة محدثة تستخدم ملف JSON للمحافظات
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
from .models import Candidate, ElectoralPromise, PublicServiceHistory, Message, Rating, Vote, News, ActivityLog, FeaturedCandidate
from .utils import load_governorates_data, get_governorate_by_id, get_governorate_by_slug, search_governorates
import json
import os
from django.conf import settings


def home(request):
    """
    الصفحة الرئيسية للموقع (Landing Page)
    """
    featured_candidates = Candidate.objects.filter(is_featured=True).order_by("name")[:6]
    context = {
        'page_title': 'الصفحة الرئيسية',
        'meta_description': 'نائبك دوت كوم - حلقة الوصل بين المواطن ونائب مجلس النواب في جمهورية مصر العربية',
        'featured_candidates': featured_candidates,
    }
    return render(request, 'naebak/index.html', context)


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
        
        governorates_with_stats.append({
            'governorate': governorate,
            'total_candidates': total_candidates,
            'total_messages': total_messages,
            'total_votes': total_votes,
            'total_ratings': total_ratings,
            'total_activity': total_activity,
            'avg_rating': round(avg_governorate_rating, 1),
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
    return render(request, 'naebak/governorates.html', context)


def governorate_detail(request, slug):
    """
    صفحة تفاصيل محافظة معينة - تستخدم ملف JSON
    """
    governorate = get_governorate_by_slug(slug)
    if not governorate:
        messages.error(request, 'المحافظة المطلوبة غير موجودة.')
        return redirect('governorates')
    
    # Get candidates for this governorate
    candidates = Candidate.objects.filter(governorate_id=governorate['id'])
    featured_candidates = candidates.filter(is_featured=True)[:6]
    other_candidates = candidates.filter(is_featured=False)
    
    context = {
        'page_title': f"محافظة {governorate['name_ar']}",
        'governorate': governorate,
        'featured_candidates': featured_candidates,
        'other_candidates': other_candidates,
        'total_candidates': candidates.count(),
    }
    return render(request, 'naebak/governorate_detail.html', context)


def candidates(request):
    """
    صفحة قائمة المرشحين مع البحث المتقدم
    """
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    governorate_id = request.GET.get('governorate', '').strip()
    sort_by = request.GET.get('sort', 'name')  # name, rating, activity, votes
    
    # Start with all candidates
    candidates_list = Candidate.objects.select_related('user').prefetch_related('ratings', 'votes', 'messages')
    
    # Apply search filter
    if search_query:
        candidates_list = candidates_list.filter(
            Q(name__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(constituency__icontains=search_query) |
            Q(election_symbol__icontains=search_query) |
            Q(electoral_program__icontains=search_query)
        )
    
    # Apply governorate filter
    if governorate_id:
        try:
            gov_id = int(governorate_id)
            candidates_list = candidates_list.filter(governorate_id=gov_id)
        except ValueError:
            pass
    
    # Apply sorting with annotations
    if sort_by == 'rating':
        candidates_list = candidates_list.annotate(
            avg_rating=Avg('ratings__stars'),
            ratings_count=Count('ratings')
        ).order_by('-avg_rating', '-ratings_count', 'name')
    elif sort_by == 'activity':
        candidates_list = candidates_list.annotate(
            total_messages=Count('messages'),
            total_votes=Count('votes'),
            total_ratings=Count('ratings'),
            total_activity=Count('messages') + Count('votes') + Count('ratings')
        ).order_by('-total_activity', 'name')
    elif sort_by == 'votes':
        candidates_list = candidates_list.annotate(
            total_votes=Count('votes'),
            approve_votes=Count('votes', filter=Q(votes__vote_type='approve')),
            disapprove_votes=Count('votes', filter=Q(votes__vote_type='disapprove'))
        ).order_by('-total_votes', 'name')
    else:
        # Default sort by name
        candidates_list = candidates_list.order_by('name')
    
    # Pagination
    paginator = Paginator(candidates_list, 12)  # 12 candidates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Load governorates for filter dropdown
    governorates = load_governorates_data()
    
    context = {
        'page_title': 'المرشحون',
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_governorate': governorate_id,
        'sort_by': sort_by,
        'governorates': governorates,
        'total_candidates': candidates_list.count(),
    }
    return render(request, 'naebak/candidates.html', context)


def candidate_detail(request, pk):
    """
    صفحة تفاصيل مرشح معين
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Get candidate statistics
    ratings = candidate.ratings.all()
    votes = candidate.votes.all()
    messages_count = candidate.messages.count()
    
    # Calculate rating statistics
    total_ratings = ratings.count()
    avg_rating = ratings.aggregate(avg=Avg('stars'))['avg'] or 0
    rating_distribution = {i: ratings.filter(stars=i).count() for i in range(1, 6)}
    
    # Calculate vote statistics
    total_votes = votes.count()
    approve_votes = votes.filter(vote_type='approve').count()
    disapprove_votes = votes.filter(vote_type='disapprove').count()
    approval_percentage = (approve_votes / total_votes * 100) if total_votes > 0 else 0
    
    # Check if current user has already rated or voted
    user_rating = None
    user_vote = None
    if request.user.is_authenticated:
        try:
            user_rating = ratings.get(citizen=request.user)
        except Rating.DoesNotExist:
            pass
        
        try:
            user_vote = votes.get(citizen=request.user)
        except Vote.DoesNotExist:
            pass
    
    # Get recent ratings with comments
    recent_ratings = ratings.exclude(comment='').order_by('-timestamp')[:5]
    
    context = {
        'page_title': f"المرشح {candidate.name}",
        'candidate': candidate,
        'total_ratings': total_ratings,
        'avg_rating': round(avg_rating, 1),
        'rating_distribution': rating_distribution,
        'total_votes': total_votes,
        'approve_votes': approve_votes,
        'disapprove_votes': disapprove_votes,
        'approval_percentage': round(approval_percentage, 1),
        'messages_count': messages_count,
        'user_rating': user_rating,
        'user_vote': user_vote,
        'recent_ratings': recent_ratings,
    }
    return render(request, 'naebak/candidate_detail.html', context)


# Authentication Views
def login_view(request):
    """
    صفحة تسجيل الدخول
    """
    next_url = request.GET.get("next", "naebak:home")
    if request.user.is_authenticated:
        return redirect("naebak:home")
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'مرحباً بك {user.get_full_name() or user.username}!')
            
            # Log the login activity
            ActivityLog.log_activity(
                user=user,
                action_type='login',
                description=f'تسجيل دخول ناجح للمستخدم {user.username}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_key=request.session.session_key
            )
            
            return redirect(next_url)
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
            
            # Log failed login attempt
            ActivityLog.log_activity(
                user=None,
                action_type='login',
                description=f'محاولة تسجيل دخول فاشلة لاسم المستخدم: {username}',
                severity='warning',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                extra_data={'attempted_username': username}
            )
    
    context = {
        'page_title': 'تسجيل الدخول',
    }
    return render(request, 'naebak/login.html', context)


def register_view(request):
    """
    صفحة تسجيل حساب جديد
    """
    if request.user.is_authenticated:
        return redirect('naebak:home')
    
    if request.method == 'POST':

        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if not email:
            messages.error(request, 'البريد الإلكتروني لا يمكن أن يكون فارغاً.')
        elif password1 != password2:
            messages.error(request, 'كلمتا المرور غير متطابقتان.')
        elif User.objects.filter(username=email).exists():
            messages.error(request, 'اسم المستخدم موجود بالفعل.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني مستخدم بالفعل.')
        else:
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password1
            )
            
            # Automatically log in the user after registration
            login(request, user)
            
            # Log the registration
            ActivityLog.log_activity(
                user=user,
                action_type='register',
                description=f'تسجيل حساب جديد للمستخدم {user.username}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                content_object=user
            )
            
            messages.success(request, f'مرحباً بك {user.get_full_name()}! تم إنشاء حسابك بنجاح وتسجيل دخولك تلقائياً.')
            return redirect('naebak:home')
    
    context = {
        'page_title': 'إنشاء حساب جديد',
    }
    return render(request, 'naebak/register.html', context)


@login_required
def logout_view(request):
    """
    تسجيل الخروج
    """
    # Log the logout activity
    ActivityLog.log_activity(
        user=request.user,
        action_type='logout',
        description=f'تسجيل خروج للمستخدم {request.user.username}',
        ip_address=request.META.get('REMOTE_ADDR'),
        session_key=request.session.session_key
    )
    
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح.')
    return redirect('naebak:home')


@login_required
def profile_view(request):
    """
    صفحة الملف الشخصي للمستخدم
    """
    user = request.user
    
    # Get user statistics
    user_ratings = Rating.objects.filter(citizen=user)
    user_votes = Vote.objects.filter(citizen=user)
    user_messages = Message.objects.filter(sender_user=user)
    
    context = {
        'page_title': 'الملف الشخصي',
        'user': user,
        'total_ratings': user_ratings.count(),
        'total_votes': user_votes.count(),
        'total_messages': user_messages.count(),
        'recent_ratings': user_ratings.order_by('-timestamp')[:5],
        'recent_votes': user_votes.order_by('-timestamp')[:5],
        'recent_messages': user_messages.order_by('-timestamp')[:5],
    }
    return render(request, 'naebak/profile.html', context)


# Candidate Dashboard Views
@login_required
def candidate_dashboard(request):
    """
    لوحة تحكم المرشح
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    # Get statistics
    total_messages = candidate.messages.count()
    unread_messages = candidate.messages.filter(is_read=False).count()
    total_ratings = candidate.ratings.count()
    avg_rating = candidate.ratings.aggregate(avg=Avg('stars'))['avg'] or 0
    total_votes = candidate.votes.count()
    approve_votes = candidate.votes.filter(vote_type='approve').count()
    approval_percentage = (approve_votes / total_votes * 100) if total_votes > 0 else 0
    
    # Calculate profile completion
    profile_fields = [
        candidate.profile_picture,
        candidate.banner_image,
        candidate.bio,
        candidate.electoral_program,
        candidate.message_to_voters,
        candidate.phone_number,
    ]
    completed_fields = sum(1 for field in profile_fields if field)
    profile_completion = (completed_fields / len(profile_fields)) * 100
    
    context = {
        'page_title': 'لوحة التحكم',
        'candidate': candidate,
        'total_messages': total_messages,
        'unread_messages': unread_messages,
        'total_ratings': total_ratings,
        'avg_rating': round(avg_rating, 1),
        'total_votes': total_votes,
        'approve_votes': approve_votes,
        'approval_percentage': round(approval_percentage, 1),
        'profile_completion': round(profile_completion, 1),
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
        # Update candidate information
        candidate.name = request.POST.get('name', candidate.name)
        candidate.bio = request.POST.get('bio', candidate.bio)
        candidate.constituency = request.POST.get('constituency', candidate.constituency)
        candidate.election_number = request.POST.get('election_number', candidate.election_number)
        candidate.election_symbol = request.POST.get('election_symbol', candidate.election_symbol)
        candidate.electoral_program = request.POST.get('electoral_program', candidate.electoral_program)
        candidate.message_to_voters = request.POST.get('message_to_voters', candidate.message_to_voters)
        candidate.youtube_video_url = request.POST.get('youtube_video_url', candidate.youtube_video_url)
        candidate.facebook_url = request.POST.get('facebook_url', candidate.facebook_url)
        candidate.twitter_url = request.POST.get('twitter_url', candidate.twitter_url)
        candidate.website_url = request.POST.get('website_url', candidate.website_url)
        candidate.phone_number = request.POST.get('phone_number', candidate.phone_number)
        
        # Handle governorate change
        governorate_id = request.POST.get('governorate_id')
        if governorate_id:
            try:
                candidate.governorate_id = int(governorate_id)
            except ValueError:
                pass
        
        # Handle file uploads
        if 'profile_picture' in request.FILES:
            candidate.profile_picture = request.FILES['profile_picture']
        
        if 'banner_image' in request.FILES:
            candidate.banner_image = request.FILES['banner_image']
        
        candidate.save()
        
        # Log the profile update
        ActivityLog.log_activity(
            user=request.user,
            action_type='profile_update',
            description=f'تحديث الملف الشخصي للمرشح {candidate.name}',
            content_object=candidate
        )
        
        messages.success(request, 'تم تحديث الملف الشخصي بنجاح!')
        return redirect('candidate_dashboard')
    
    # Load governorates for dropdown
    governorates = load_governorates_data()
    
    context = {
        'page_title': 'تعديل الملف الشخصي',
        'candidate': candidate,
        'governorates': governorates,
    }
    return render(request, 'naebak/candidate_profile_edit.html', context)


@login_required
def candidate_electoral_program(request):
    """
    صفحة إدارة البرنامج الانتخابي
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        candidate.electoral_program = request.POST.get('electoral_program', candidate.electoral_program)
        candidate.save()
        
        # Log the update
        ActivityLog.log_activity(
            user=request.user,
            action_type='candidate_updated',
            description=f'تحديث البرنامج الانتخابي للمرشح {candidate.name}',
            content_object=candidate
        )
        
        messages.success(request, 'تم تحديث البرنامج الانتخابي بنجاح!')
        return redirect('candidate_electoral_program')
    
    context = {
        'page_title': 'البرنامج الانتخابي',
        'candidate': candidate,
    }
    return render(request, 'naebak/candidate_electoral_program.html', context)


@login_required
def candidate_promises(request):
    """
    صفحة إدارة الوعود الانتخابية
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_promise':
            title = request.POST.get('title')
            description = request.POST.get('description')
            
            if title and description:
                ElectoralPromise.objects.create(
                    candidate=candidate,
                    title=title,
                    description=description,
                    order=candidate.electoral_promises.count() + 1
                )
                
                # Log the creation
                ActivityLog.log_activity(
                    user=request.user,
                    action_type='promise_created',
                    description=f'إضافة وعد انتخابي جديد: {title}',
                    content_object=candidate
                )
                
                messages.success(request, 'تم إضافة الوعد الانتخابي بنجاح!')
            else:
                messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
        
        return redirect('candidate_promises')
    
    promises = candidate.electoral_promises.all().order_by('order')
    
    context = {
        'page_title': 'الوعود الانتخابية',
        'candidate': candidate,
        'promises': promises,
    }
    return render(request, 'naebak/candidate_promises.html', context)


@login_required
def delete_promise(request, promise_id):
    """
    حذف وعد انتخابي
    """
    try:
        candidate = request.user.candidate_profile
        promise = get_object_or_404(ElectoralPromise, id=promise_id, candidate=candidate)
        
        # Log the deletion
        ActivityLog.log_activity(
            user=request.user,
            action_type='promise_deleted',
            description=f'حذف وعد انتخابي: {promise.title}',
            content_object=candidate
        )
        
        promise.delete()
        messages.success(request, 'تم حذف الوعد الانتخابي بنجاح!')
        
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
    
    return redirect('candidate_promises')


@login_required
def candidate_messages(request):
    """
    صفحة رسائل المرشح
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    # Get messages with pagination
    messages_list = candidate.messages.all().order_by('-timestamp')
    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Mark messages as read when viewed
    unread_messages = messages_list.filter(is_read=False)
    unread_messages.update(is_read=True)
    
    context = {
        'page_title': 'الرسائل الواردة',
        'candidate': candidate,
        'page_obj': page_obj,
        'total_messages': messages_list.count(),
    }
    return render(request, 'naebak/candidate_messages.html', context)


@login_required
def candidate_ratings_votes(request):
    """
    صفحة التقييمات والتصويتات
    """
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    # Get ratings and votes
    ratings = candidate.ratings.all().order_by('-timestamp')
    votes = candidate.votes.all().order_by('-timestamp')
    
    # Calculate statistics
    total_ratings = ratings.count()
    avg_rating = ratings.aggregate(avg=Avg('stars'))['avg'] or 0
    rating_distribution = {i: ratings.filter(stars=i).count() for i in range(1, 6)}
    
    total_votes = votes.count()
    approve_votes = votes.filter(vote_type='approve').count()
    disapprove_votes = votes.filter(vote_type='disapprove').count()
    approval_percentage = (approve_votes / total_votes * 100) if total_votes > 0 else 0
    
    # Pagination for ratings and votes
    ratings_paginator = Paginator(ratings, 5)
    ratings_page = request.GET.get('ratings_page')
    ratings_page_obj = ratings_paginator.get_page(ratings_page)
    
    votes_paginator = Paginator(votes, 10)
    votes_page = request.GET.get('votes_page')
    votes_page_obj = votes_paginator.get_page(votes_page)
    
    context = {
        'page_title': 'التقييمات والتصويتات',
        'candidate': candidate,
        'total_ratings': total_ratings,
        'avg_rating': round(avg_rating, 1),
        'rating_distribution': rating_distribution,
        'total_votes': total_votes,
        'approve_votes': approve_votes,
        'disapprove_votes': disapprove_votes,
        'approval_percentage': round(approval_percentage, 1),
        'ratings_page_obj': ratings_page_obj,
        'votes_page_obj': votes_page_obj,
    }
    return render(request, 'naebak/candidate_ratings_votes.html', context)


# Message and Rating Views
@login_required
def send_message_to_candidate(request, candidate_id):
    """
    إرسال رسالة لمرشح
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        attachment = request.FILES.get('attachment')
        
        if subject and content:
            message = Message.objects.create(
                candidate=candidate,
                sender_user=request.user,
                sender_name=request.user.get_full_name() or request.user.username,
                sender_email=request.user.email,
                subject=subject,
                content=content,
                attachment=attachment
            )
            
            # Log the message sending
            ActivityLog.log_activity(
                user=request.user,
                action_type='message_sent',
                description=f'إرسال رسالة للمرشح {candidate.name}: {subject}',
                content_object=message
            )
            
            messages.success(request, 'تم إرسال الرسالة بنجاح!')
            return redirect('candidate_detail', candidate_id=candidate.id)
        else:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
    
    context = {
        'page_title': f'إرسال رسالة للمرشح {candidate.name}',
        'candidate': candidate,
    }
    return render(request, 'naebak/send_message.html', context)


@login_required
@require_POST
def rate_candidate(request, candidate_id):
    """
    تقييم مرشح
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    stars = request.POST.get('stars')
    comment = request.POST.get('comment', '')
    
    try:
        stars = int(stars)
        if not (1 <= stars <= 5):
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, 'تقييم غير صحيح.')
        return redirect('candidate_detail', candidate_id=candidate.id)
    
    # Update or create rating
    rating, created = Rating.objects.update_or_create(
        candidate=candidate,
        citizen=request.user,
        defaults={
            'stars': stars,
            'comment': comment,
        }
    )
    
    # Log the rating
    action = 'rating_given' if created else 'rating_updated'
    ActivityLog.log_activity(
        user=request.user,
        action_type=action,
        description=f'تقييم المرشح {candidate.name} بـ {stars} نجوم',
        content_object=rating
    )
    
    if created:
        messages.success(request, 'تم إضافة تقييمك بنجاح!')
    else:
        messages.success(request, 'تم تحديث تقييمك بنجاح!')
    
    return redirect('candidate_detail', candidate_id=candidate.id)


@login_required
@require_POST
def vote_candidate(request, candidate_id):
    """
    التصويت لمرشح (تأييد أو معارضة)
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in ['approve', 'disapprove']:
        messages.error(request, 'نوع تصويت غير صحيح.')
        return redirect('candidate_detail', candidate_id=candidate.id)
    
    # Update or create vote
    vote, created = Vote.objects.update_or_create(
        candidate=candidate,
        citizen=request.user,
        defaults={'vote_type': vote_type}
    )
    
    # Log the vote
    action = 'vote_cast' if created else 'vote_updated'
    vote_text = 'تأييد' if vote_type == 'approve' else 'معارضة'
    ActivityLog.log_activity(
        user=request.user,
        action_type=action,
        description=f'{vote_text} المرشح {candidate.name}',
        content_object=vote
    )
    
    if created:
        messages.success(request, f'تم تسجيل {vote_text}ك بنجاح!')
    else:
        messages.success(request, f'تم تحديث {vote_text}ك بنجاح!')
    
    return redirect('candidate_detail', candidate_id=candidate.id)


# Admin Views
@login_required
def admin_panel(request):
    """
    لوحة تحكم الإدارة
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    # Get statistics
    total_users = User.objects.count()
    total_candidates = Candidate.objects.count()
    total_messages = Message.objects.count()
    total_ratings = Rating.objects.count()
    total_votes = Vote.objects.count()
    total_news = News.objects.count()
    
    # Get recent activities
    recent_activities = ActivityLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    context = {
        'page_title': 'لوحة تحكم الإدارة',
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_messages': total_messages,
        'total_ratings': total_ratings,
        'total_votes': total_votes,
        'total_news': total_news,
        'recent_activities': recent_activities,
    }
    return render(request, 'naebak/admin_panel.html', context)


@login_required
def user_management(request):
    """
    إدارة المستخدمين
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    # Start with all users
    users_list = User.objects.all().order_by('-date_joined')
    
    # Apply search filter
    if search_query:
        users_list = users_list.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Apply role filter
    if role_filter == 'candidate':
        users_list = users_list.filter(candidate_profile__isnull=False)
    elif role_filter == 'citizen':
        users_list = users_list.filter(candidate_profile__isnull=True, is_staff=False)
    elif role_filter == 'admin':
        users_list = users_list.filter(is_staff=True)
    
    # Apply status filter
    if status_filter == 'active':
        users_list = users_list.filter(is_active=True)
    elif status_filter == 'inactive':
        users_list = users_list.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(users_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'إدارة المستخدمين',
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_users': users_list.count(),
    }
    return render(request, 'naebak/user_management.html', context)


@login_required
def create_candidate(request):
    """
    إنشاء حساب مرشح جديد
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        # User information

        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Candidate information
        candidate_name = request.POST.get('candidate_name')
        governorate_id = request.POST.get('governorate_id')
        constituency = request.POST.get('constituency')
        election_number = request.POST.get('election_number')
        election_symbol = request.POST.get('election_symbol')
        
        # Validation
        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود بالفعل.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني مستخدم بالفعل.')
        else:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password
                )
                
                # Create candidate profile
                candidate = Candidate.objects.create(
                    user=user,
                    name=candidate_name,
                    governorate_id=int(governorate_id),
                    constituency=constituency,
                    election_number=election_number,
                    election_symbol=election_symbol
                )
                
                # Log the creation
                ActivityLog.log_activity(
                    user=request.user,
                    action_type='candidate_created',
                    description=f'إنشاء حساب مرشح جديد: {candidate_name}',
                    content_object=candidate
                )
                
                messages.success(request, f'تم إنشاء حساب المرشح {candidate_name} بنجاح!')
                return redirect('user_management')
                
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {str(e)}')
    
    # Load governorates for dropdown
    governorates = load_governorates_data()
    
    context = {
        'page_title': 'إنشاء حساب مرشح جديد',
        'governorates': governorates,
    }
    return render(request, 'naebak/create_candidate.html', context)


# News Management Views
@login_required
def news_management(request):
    """
    إدارة الأخبار
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    # Get search parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    
    # Start with all news
    news_list = News.objects.all().order_by('-created_at')
    
    # Apply filters
    if search_query:
        news_list = news_list.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    if status_filter:
        news_list = news_list.filter(status=status_filter)
    
    if priority_filter:
        news_list = news_list.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(news_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_news = News.objects.count()
    published_news = News.objects.filter(status='published').count()
    draft_news = News.objects.filter(status='draft').count()
    urgent_news = News.objects.filter(priority='urgent').count()
    
    context = {
        'page_title': 'إدارة الأخبار',
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'total_news': total_news,
        'published_news': published_news,
        'draft_news': draft_news,
        'urgent_news': urgent_news,
    }
    return render(request, 'naebak/news_management.html', context)


@login_required
def create_news(request):
    """
    إنشاء خبر جديد
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        status = request.POST.get('status', 'draft')
        priority = request.POST.get('priority', 'normal')
        show_on_homepage = request.POST.get('show_on_homepage') == 'on'
        show_on_ticker = request.POST.get('show_on_ticker') == 'on'
        ticker_speed = request.POST.get('ticker_speed', 50)
        meta_description = request.POST.get('meta_description', '')
        tags = request.POST.get('tags', '')
        
        if title and content:
            news = News.objects.create(
                title=title,
                content=content,
                status=status,
                priority=priority,
                show_on_homepage=show_on_homepage,
                show_on_ticker=show_on_ticker,
                ticker_speed=int(ticker_speed),
                meta_description=meta_description,
                tags=tags,
                author=request.user
            )
            
            # Log the creation
            ActivityLog.log_activity(
                user=request.user,
                action_type='news_created',
                description=f'إنشاء خبر جديد: {title}',
                content_object=news
            )
            
            messages.success(request, 'تم إنشاء الخبر بنجاح!')
            return redirect('news_management')
        else:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
    
    context = {
        'page_title': 'إنشاء خبر جديد',
    }
    return render(request, 'naebak/create_news.html', context)


# Activity Monitoring Views
@login_required
def activity_monitoring(request):
    """
    مراقبة النشاط
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    # Get filter parameters
    action_filter = request.GET.get('action', '').strip()
    severity_filter = request.GET.get('severity', '').strip()
    user_filter = request.GET.get('user', '').strip()
    date_filter = request.GET.get('date', '').strip()
    search_query = request.GET.get('search', '').strip()
    
    # Start with all activities
    activities = ActivityLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply filters
    if action_filter:
        activities = activities.filter(action_type=action_filter)
    
    if severity_filter:
        activities = activities.filter(severity=severity_filter)
    
    if user_filter:
        try:
            user_id = int(user_filter)
            activities = activities.filter(user_id=user_id)
        except ValueError:
            pass
    
    if search_query:
        activities = activities.filter(
            Q(description__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_activities = ActivityLog.objects.count()
    critical_activities = ActivityLog.objects.filter(severity='critical').count()
    error_activities = ActivityLog.objects.filter(severity='error').count()
    warning_activities = ActivityLog.objects.filter(severity='warning').count()
    
    # Get recent security alerts
    security_alerts = ActivityLog.get_security_alerts(10)
    
    context = {
        'page_title': 'مراقبة النشاط',
        'page_obj': page_obj,
        'action_filter': action_filter,
        'severity_filter': severity_filter,
        'user_filter': user_filter,
        'search_query': search_query,
        'total_activities': total_activities,
        'critical_activities': critical_activities,
        'error_activities': error_activities,
        'warning_activities': warning_activities,
        'security_alerts': security_alerts,
        'action_choices': ActivityLog.ACTION_TYPES,
        'severity_choices': ActivityLog.SEVERITY_LEVELS,
    }
    return render(request, 'naebak/activity_monitoring.html', context)


# Reports and Statistics Views
@login_required
def reports_dashboard(request):
    """
    لوحة التقارير والإحصائيات
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    # Get date range filter
    days = int(request.GET.get('days', 30))
    
    from django.utils import timezone
    from datetime import timedelta
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # General statistics
    total_users = User.objects.count()
    total_candidates = Candidate.objects.count()
    total_messages = Message.objects.count()
    total_ratings = Rating.objects.count()
    total_votes = Vote.objects.count()
    
    # Period statistics
    new_users = User.objects.filter(date_joined__gte=start_date).count()
    new_messages = Message.objects.filter(timestamp__gte=start_date).count()
    new_ratings = Rating.objects.filter(timestamp__gte=start_date).count()
    new_votes = Vote.objects.filter(timestamp__gte=start_date).count()
    
    # Top candidates by engagement
    top_candidates = Candidate.objects.annotate(
        total_messages=Count('messages'),
        total_ratings=Count('ratings'),
        total_votes=Count('votes'),
        avg_rating=Avg('ratings__stars'),
        total_engagement=Count('messages') + Count('ratings') + Count('votes')
    ).order_by('-total_engagement')[:10]
    
    # Governorate statistics
    governorates_data = []
    governorates = load_governorates_data()
    
    for gov in governorates:
        candidates_count = Candidate.objects.filter(governorate_id=gov['id']).count()
        if candidates_count > 0:
            governorates_data.append({
                'name': gov['name_ar'],
                'candidates_count': candidates_count,
            })
    
    governorates_data.sort(key=lambda x: x['candidates_count'], reverse=True)
    
    # System health indicators
    recent_errors = ActivityLog.objects.filter(
        severity__in=['error', 'critical'],
        timestamp__gte=start_date
    ).count()
    
    system_health = 'excellent' if recent_errors == 0 else 'good' if recent_errors < 5 else 'warning' if recent_errors < 20 else 'critical'
    
    context = {
        'page_title': 'التقارير والإحصائيات',
        'days': days,
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_messages': total_messages,
        'total_ratings': total_ratings,
        'total_votes': total_votes,
        'new_users': new_users,
        'new_messages': new_messages,
        'new_ratings': new_ratings,
        'new_votes': new_votes,
        'top_candidates': top_candidates,
        'governorates_data': governorates_data[:10],
        'system_health': system_health,
        'recent_errors': recent_errors,
    }
    return render(request, 'naebak/reports_dashboard.html', context)


# API Views
@require_GET
def get_ticker_news(request):
    """
    API لجلب أخبار الشريط الإخباري
    """
    news = News.get_ticker_news().values('title', 'content', 'priority')
    return JsonResponse({'news': list(news)})


# Utility Views
def privacy_policy(request):
    """
    صفحة سياسة الخصوصية
    """
    context = {
        'page_title': 'سياسة الخصوصية',
    }
    return render(request, 'naebak/privacy_policy.html', context)


def terms_of_service(request):
    """
    صفحة شروط الاستخدام
    """
    context = {
        'page_title': 'شروط الاستخدام',
    }
    return render(request, 'naebak/terms_of_service.html', context)


def robots_txt(request):
    """
    ملف robots.txt
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /candidate/",
        "",
        "Sitemap: https://naebak.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")




# Additional Views for URL compatibility
def governorate_candidates_list(request, slug):
    """
    قائمة مرشحي محافظة معينة
    """
    governorate = get_governorate_by_slug(slug)
    if not governorate:
        messages.error(request, 'المحافظة المطلوبة غير موجودة.')
        return redirect('governorates')
    
    candidates = Candidate.objects.filter(governorate_id=governorate['id']).order_by('name')
    
    context = {
        'page_title': f"مرشحو محافظة {governorate['name_ar']}",
        'governorate': governorate,
        'candidates': candidates,
    }
    return render(request, 'naebak/governorate_candidates_list.html', context)


def candidate_profile(request):
    """
    الملف الشخصي العام للمرشح (للمواطنين)
    """
    return redirect('candidates')


def citizen_register(request):
    """
    تسجيل حساب مواطن جديد
    """
    return register_view(request)


def citizen_profile(request):
    """
    الملف الشخصي للمواطن
    """
    return profile_view(request)


def conversations(request):
    """
    المحادثات
    """
    return redirect('my_messages')


def my_messages(request):
    """
    رسائلي
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get user's sent messages
    sent_messages = Message.objects.filter(sender_user=request.user).order_by('-timestamp')
    
    context = {
        'page_title': 'رسائلي',
        'sent_messages': sent_messages,
    }
    return render(request, 'naebak/my_messages.html', context)


def message_thread(request, message_id):
    """
    سلسلة المحادثات
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to view this message
    if not (request.user == message.sender_user or 
            (hasattr(request.user, 'candidate_profile') and 
             request.user.candidate_profile == message.candidate)):
        messages.error(request, 'ليس لديك صلاحية لعرض هذه الرسالة.')
        return redirect('naebak:home')
    
    context = {
        'page_title': f'الرسالة: {message.subject}',
        'message': message,
    }
    return render(request, 'naebak/message_thread.html', context)


def get_notifications(request):
    """
    API لجلب الإشعارات
    """
    if not request.user.is_authenticated:
        return JsonResponse({'notifications': []})
    
    # Simple notification system - can be expanded
    notifications = []
    
    # For candidates, show unread messages count
    if hasattr(request.user, 'candidate_profile'):
        candidate = request.user.candidate_profile
        unread_count = candidate.messages.filter(is_read=False).count()
        if unread_count > 0:
            notifications.append({
                'type': 'message',
                'count': unread_count,
                'text': f'لديك {unread_count} رسالة جديدة',
                'url': '/candidate/messages/'
            })
    
    return JsonResponse({'notifications': notifications})


def mark_notification_read(request):
    """
    تمييز إشعار كمقروء
    """
    return JsonResponse({'status': 'success'})


def mark_all_notifications_read(request):
    """
    تمييز جميع الإشعارات كمقروءة
    """
    return JsonResponse({'status': 'success'})


def backup_data(request):
    """
    نسخ احتياطي للبيانات
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    messages.info(request, 'ميزة النسخ الاحتياطي قيد التطوير.')
    return redirect('admin_panel')


def restore_data(request):
    """
    استعادة البيانات
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    messages.info(request, 'ميزة استعادة البيانات قيد التطوير.')
    return redirect('admin_panel')


def manage_candidates(request):
    """
    إدارة المرشحين
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    candidates = Candidate.objects.select_related('user').all().order_by('name')
    
    context = {
        'page_title': 'إدارة المرشحين',
        'candidates': candidates,
    }
    return render(request, 'naebak/manage_candidates.html', context)


def delete_candidate(request, candidate_id):
    """
    حذف مرشح
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    candidate = get_object_or_404(Candidate, pk=pk)
    
    if request.method == 'POST':
        # Log the deletion
        ActivityLog.log_activity(
            user=request.user,
            action_type='candidate_deleted',
            description=f'حذف حساب المرشح {candidate.name}',
            severity='warning'
        )
        
        # Delete the user account (this will cascade delete the candidate)
        candidate.user.delete()
        messages.success(request, f'تم حذف حساب المرشح {candidate.name} بنجاح!')
    
    return redirect('manage_candidates')


def create_governorates_data(request):
    """
    إنشاء بيانات المحافظات (للتطوير فقط)
    """
    messages.info(request, 'بيانات المحافظات محفوظة في ملف JSON ولا تحتاج إنشاء.')
    return redirect('naebak:home')


def user_login(request):
    """
    تسجيل الدخول
    """
    return login_view(request)


def user_logout(request):
    """
    تسجيل الخروج
    """
    return logout_view(request)


def candidate_message_reply(request, message_id):
    """
    الرد على رسالة
    """
    try:
        candidate = request.user.candidate_profile
        message = get_object_or_404(Message, id=message_id, candidate=candidate)
    except Candidate.DoesNotExist:
        messages.error(request, 'هذا الحساب غير مخصص للمرشحين.')
        return redirect('naebak:home')
    
    if request.method == 'POST':
        reply_content = request.POST.get('reply_content')
        if reply_content:
            # Create reply message
            reply = Message.objects.create(
                candidate=candidate,
                sender_user=request.user,
                sender_name=candidate.name,
                sender_email=request.user.email,
                subject=f'رد: {message.subject}',
                content=reply_content,
                reply_to=message
            )
            
            # Log the reply
            ActivityLog.log_activity(
                user=request.user,
                action_type='message_reply',
                description=f'رد على رسالة: {message.subject}',
                content_object=reply
            )
            
            messages.success(request, 'تم إرسال الرد بنجاح!')
            return redirect('candidate_messages')
    
    context = {
        'page_title': f'الرد على: {message.subject}',
        'message': message,
        'candidate': candidate,
    }
    return render(request, 'naebak/candidate_message_reply.html', context)


# News Management Functions
def edit_news(request, news_id):
    """
    تعديل خبر
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    news = get_object_or_404(News, id=news_id)
    
    if request.method == 'POST':
        news.title = request.POST.get('title', news.title)
        news.content = request.POST.get('content', news.content)
        news.status = request.POST.get('status', news.status)
        news.priority = request.POST.get('priority', news.priority)
        news.show_on_homepage = request.POST.get('show_on_homepage') == 'on'
        news.show_on_ticker = request.POST.get('show_on_ticker') == 'on'
        news.meta_description = request.POST.get('meta_description', news.meta_description)
        news.tags = request.POST.get('tags', news.tags)
        
        news.save()
        
        # Log the update
        ActivityLog.log_activity(
            user=request.user,
            action_type='news_updated',
            description=f'تحديث الخبر: {news.title}',
            content_object=news
        )
        
        messages.success(request, 'تم تحديث الخبر بنجاح!')
        return redirect('news_management')
    
    context = {
        'page_title': f'تعديل الخبر: {news.title}',
        'news': news,
    }
    return render(request, 'naebak/edit_news.html', context)


def delete_news(request, news_id):
    """
    حذف خبر
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    news = get_object_or_404(News, id=news_id)
    
    if request.method == 'POST':
        # Log the deletion
        ActivityLog.log_activity(
            user=request.user,
            action_type='news_deleted',
            description=f'حذف الخبر: {news.title}',
            severity='warning'
        )
        
        news.delete()
        messages.success(request, 'تم حذف الخبر بنجاح!')
    
    return redirect('news_management')


def toggle_news_status(request, news_id):
    """
    تغيير حالة الخبر
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'غير مصرح'}, status=403)
    
    news = get_object_or_404(News, id=news_id)
    
    # Toggle between published and draft
    if news.status == 'published':
        news.status = 'draft'
    else:
        news.status = 'published'
    
    news.save()
    
    # Log the status change
    ActivityLog.log_activity(
        user=request.user,
        action_type='news_updated',
        description=f'تغيير حالة الخبر "{news.title}" إلى {news.get_status_display()}',
        content_object=news
    )
    
    return JsonResponse({
        'status': 'success',
        'new_status': news.status,
        'new_status_display': news.get_status_display()
    })


def news_detail(request, news_id):
    """
    تفاصيل خبر
    """
    news = get_object_or_404(News, id=news_id)
    
    # Increment views count
    news.increment_views()
    
    context = {
        'page_title': news.title,
        'news': news,
    }
    return render(request, 'naebak/news_detail.html', context)


# Activity Monitoring Functions
def activity_detail(request, activity_id):
    """
    تفاصيل نشاط
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    activity = get_object_or_404(ActivityLog, id=activity_id)
    
    context = {
        'page_title': f'تفاصيل النشاط: {activity.get_action_type_display()}',
        'activity': activity,
    }
    return render(request, 'naebak/activity_detail.html', context)


def user_activity_history(request, user_id):
    """
    سجل أنشطة مستخدم
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    user = get_object_or_404(User, id=user_id)
    activities = ActivityLog.get_user_activities(user, 100)
    
    context = {
        'page_title': f'أنشطة المستخدم: {user.get_full_name() or user.username}',
        'target_user': user,
        'activities': activities,
    }
    return render(request, 'naebak/user_activity_history.html', context)


def get_activity_stats_api(request):
    """
    API لإحصائيات الأنشطة
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'غير مصرح'}, status=403)
    
    from django.utils import timezone
    from datetime import timedelta
    
    # Get activity stats for the last 24 hours
    last_24h = timezone.now() - timedelta(hours=24)
    
    stats = {
        'total_today': ActivityLog.objects.filter(timestamp__gte=last_24h).count(),
        'critical_today': ActivityLog.objects.filter(
            timestamp__gte=last_24h, 
            severity='critical'
        ).count(),
        'errors_today': ActivityLog.objects.filter(
            timestamp__gte=last_24h, 
            severity='error'
        ).count(),
        'warnings_today': ActivityLog.objects.filter(
            timestamp__gte=last_24h, 
            severity='warning'
        ).count(),
    }
    
    return JsonResponse(stats)


# Reports Functions
def candidate_performance_report(request):
    """
    تقرير أداء المرشحين
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    # Get top performing candidates
    candidates = Candidate.objects.annotate(
        total_messages=Count('messages'),
        total_ratings=Count('ratings'),
        total_votes=Count('votes'),
        avg_rating=Avg('ratings__stars'),
        total_engagement=Count('messages') + Count('ratings') + Count('votes')
    ).order_by('-total_engagement')[:20]
    
    context = {
        'page_title': 'تقرير أداء المرشحين',
        'candidates': candidates,
    }
    return render(request, 'naebak/candidate_performance_report.html', context)


def user_engagement_report(request):
    """
    تقرير تفاعل المستخدمين
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    from django.utils import timezone
    from datetime import timedelta
    
    # Get engagement stats for different periods
    periods = {
        'اليوم': timedelta(days=1),
        'الأسبوع': timedelta(days=7),
        'الشهر': timedelta(days=30),
        'الثلاثة أشهر': timedelta(days=90),
    }
    
    engagement_stats = {}
    for period_name, period_delta in periods.items():
        start_date = timezone.now() - period_delta
        
        engagement_stats[period_name] = {
            'new_users': User.objects.filter(date_joined__gte=start_date).count(),
            'active_users': User.objects.filter(last_login__gte=start_date).count(),
            'messages_sent': Message.objects.filter(timestamp__gte=start_date).count(),
            'ratings_given': Rating.objects.filter(timestamp__gte=start_date).count(),
            'votes_cast': Vote.objects.filter(timestamp__gte=start_date).count(),
        }
    
    context = {
        'page_title': 'تقرير تفاعل المستخدمين',
        'engagement_stats': engagement_stats,
    }
    return render(request, 'naebak/user_engagement_report.html', context)


def export_report_csv(request, report_type):
    """
    تصدير التقارير بصيغة CSV
    """
    if not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة.')
        return redirect('naebak:home')
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    response.write('\ufeff')  # UTF-8 BOM for Excel compatibility
    
    writer = csv.writer(response)
    
    if report_type == 'candidates':
        writer.writerow(['اسم المرشح', 'المحافظة', 'الرسائل', 'التقييمات', 'التصويتات', 'متوسط التقييم'])
        
        candidates = Candidate.objects.annotate(
            total_messages=Count('messages'),
            total_ratings=Count('ratings'),
            total_votes=Count('votes'),
            avg_rating=Avg('ratings__stars')
        )
        
        for candidate in candidates:
            writer.writerow([
                candidate.name,
                candidate.governorate_name,
                candidate.total_messages,
                candidate.total_ratings,
                candidate.total_votes,
                round(candidate.avg_rating or 0, 2)
            ])
    
    elif report_type == 'users':
        writer.writerow(['اسم المستخدم', 'الاسم الكامل', 'البريد الإلكتروني', 'تاريخ التسجيل', 'آخر دخول'])
        
        users = User.objects.all().order_by('-date_joined')
        
        for user in users:
            writer.writerow([
                user.username,
                user.get_full_name(),
                user.email,
                user.date_joined.strftime('%Y-%m-%d'),
                user.last_login.strftime('%Y-%m-%d') if user.last_login else 'لم يسجل دخول'
            ])
    
    return response


def get_chart_data_api(request):
    """
    API لبيانات الرسوم البيانية
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'غير مصرح'}, status=403)
    
    chart_type = request.GET.get('type', 'daily_activity')
    
    from django.utils import timezone
    from datetime import timedelta, date
    
    if chart_type == 'daily_activity':
        # Get daily activity for the last 30 days
        data = []
        for i in range(30):
            day = timezone.now().date() - timedelta(days=i)
            day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            
            activity_count = ActivityLog.objects.filter(
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).count()
            
            data.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': activity_count
            })
        
        return JsonResponse({'data': list(reversed(data))})
    
    elif chart_type == 'governorate_distribution':
        # Get candidate distribution by governorate
        governorates = load_governorates_data()
        data = []
        
        for gov in governorates:
            count = Candidate.objects.filter(governorate_id=gov['id']).count()
            if count > 0:
                data.append({
                    'name': gov['name_ar'],
                    'count': count
                })
        
        # Sort by count and take top 10
        data.sort(key=lambda x: x['count'], reverse=True)
        return JsonResponse({'data': data[:10]})
    
    return JsonResponse({'data': []})



@login_required
@require_POST
def rate_candidate(request, pk):
    """
    تقييم مرشح
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    stars = request.POST.get("stars")
    comment = request.POST.get("comment", "")

    if not stars:
        messages.error(request, "الرجاء اختيار عدد النجوم للتقييم.")
        return redirect("naebak:candidate_detail", pk=pk)

    try:
        stars = int(stars)
        if not (1 <= stars <= 5):
            raise ValueError
    except ValueError:
        messages.error(request, "عدد النجوم يجب أن يكون بين 1 و 5.")
        return redirect("naebak:candidate_detail", pk=pk)

    # Check if user has already rated this candidate
    existing_rating = Rating.objects.filter(candidate=candidate, citizen=request.user).first()

    if existing_rating:
        existing_rating.stars = stars
        existing_rating.comment = comment
        existing_rating.save()
        messages.success(request, "تم تحديث تقييمك بنجاح.")
        ActivityLog.log_activity(
            user=request.user,
            action_type='update_rating',
            description=f'تحديث تقييم المرشح {candidate.name} إلى {stars} نجوم',
            content_object=existing_rating
        )
    else:
        Rating.objects.create(
            candidate=candidate,
            citizen=request.user,
            stars=stars,
            comment=comment
        )
        messages.success(request, "تم إضافة تقييمك بنجاح.")
        ActivityLog.log_activity(
            user=request.user,
            action_type="add_rating",
            description=f"إضافة تقييم للمرشح {candidate.name} بـ {stars} نجوم",
            content_object=candidate
        )
    return redirect("naebak:candidate_detail", pk=pk)
@require_POST
def vote_candidate(request, pk):
    """
    التصويت لمرشح
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    vote_type = request.POST.get("vote_type")

    if vote_type not in ["approve", "disapprove"]:
        messages.error(request, "نوع التصويت غير صالح.")
        return redirect("naebak:candidate_detail", pk=pk)

    # Check if user has already voted for this candidate
    existing_vote = Vote.objects.filter(candidate=candidate, citizen=request.user).first()

    if existing_vote:
        if existing_vote.vote_type == vote_type:
            messages.info(request, "لقد قمت بالتصويت لهذا المرشح بالفعل بنفس النوع.")
        else:
            existing_vote.vote_type = vote_type
            existing_vote.save()
            messages.success(request, "تم تحديث تصويتك بنجاح.")
            ActivityLog.log_activity(
                user=request.user,
                action_type="update_vote",
                description=f"تحديث تصويت المرشح {candidate.name} إلى {vote_type}",
                content_object=existing_vote
            )
    else:
        new_vote = Vote.objects.create(
            candidate=candidate,
            citizen=request.user,
            vote_type=vote_type
        )
        messages.success(request, "تم تسجيل تصويتك بنجاح.")
        ActivityLog.log_activity(
            user=request.user,
            action_type="add_vote",
            description=f"إضافة تصويت للمرشح {candidate.name} بـ {vote_type}",
            content_object=new_vote
        )

    return redirect("naebak:candidate_detail", pk=pk)




