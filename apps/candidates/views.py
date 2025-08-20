"""
Views for candidate management and display
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

from .models import Candidate, ElectoralPromise, PublicServiceHistory, FeaturedCandidate
from apps.messaging.models import Message
from apps.voting.models import Rating, Vote, RatingReply
from apps.accounts.models import Citizen
from apps.core.models import ActivityLog
from apps.core.utils import get_governorate_by_id

import json
from django.conf import settings


def candidate_list(request):
    """
    صفحة قائمة جميع المرشحين مع البحث والفلترة
    """
    # Get search and filter parameters
    search_query = request.GET.get("search", "").strip()
    governorate_id = request.GET.get("governorate_id")
    sort_by = request.GET.get("sort", "name")  # name, rating, votes, activity
    
    # Start with all candidates
    candidates = Candidate.objects.all()
    
    # Apply filters
    if search_query:
        candidates = candidates.filter(
            Q(name__icontains=search_query) |
            Q(constituency__icontains=search_query) |
            Q(bio__icontains=search_query) |
            Q(electoral_program__icontains=search_query)
        )
    
    if governorate_id:
        candidates = candidates.filter(governorate_id=governorate_id)
    
    # Calculate statistics for each candidate
    candidates_with_stats = []
    for candidate in candidates:
        # Calculate statistics
        total_votes = candidate.votes.count()
        approve_votes = candidate.votes.filter(vote_type="approve").count()
        disapprove_votes = candidate.votes.filter(vote_type="disapprove").count()
        
        ratings = candidate.ratings.all()
        avg_rating = ratings.aggregate(Avg("stars"))["stars__avg"] or 0
        total_ratings = ratings.count()
        
        total_messages = candidate.messages.count()
        total_activity = total_votes + total_ratings + total_messages
        
        candidates_with_stats.append({
            "candidate": candidate,
            "total_votes": total_votes,
            "approve_votes": approve_votes,
            "disapprove_votes": disapprove_votes,
            "avg_rating": round(avg_rating, 1),
            "total_ratings": total_ratings,
            "total_messages": total_messages,
            "total_activity": total_activity,
        })
    
    # Apply sorting
    if sort_by == "rating":
        candidates_with_stats.sort(key=lambda x: x["avg_rating"], reverse=True)
    elif sort_by == "votes":
        candidates_with_stats.sort(key=lambda x: x["total_votes"], reverse=True)
    elif sort_by == "activity":
        candidates_with_stats.sort(key=lambda x: x["total_activity"], reverse=True)
    else:
        # Default sort by name
        candidates_with_stats.sort(key=lambda x: x["candidate"].name)
    
    # Pagination
    paginator = Paginator(candidates_with_stats, 12)  # Show 12 candidates per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_title": "جميع المرشحين",
        "page_obj": page_obj,
        "search_query": search_query,
        "governorate_id": governorate_id,
        "sort_by": sort_by,
        "total_candidates": len(candidates_with_stats),
    }
    return render(request, "candidates/candidates.html", context)


def candidate_detail(request, pk):
    """
    صفحة تفاصيل مرشح معين
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Get candidate statistics
    total_votes = candidate.votes.count()
    approve_votes = candidate.votes.filter(vote_type="approve").count()
    disapprove_votes = candidate.votes.filter(vote_type="disapprove").count()
    
    ratings = candidate.ratings.all().order_by("-timestamp")
    avg_rating = ratings.aggregate(Avg("stars"))["stars__avg"] or 0
    total_ratings = ratings.count()
    
    # Get rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = ratings.filter(stars=i).count()
    
    # Get electoral promises
    electoral_promises = candidate.electoral_promises.all().order_by("order")
    
    # Get public service history
    service_history = candidate.service_history.all().order_by("-start_year")
    
    # Get recent messages (for candidate dashboard)
    recent_messages = None
    if request.user.is_authenticated and hasattr(request.user, "candidate_profile") and request.user.candidate_profile == candidate:
        recent_messages = candidate.messages.filter(is_read=False).order_by("-timestamp")[:5]
    
    # Check if current user has already voted/rated
    user_vote = None
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_vote = candidate.votes.get(citizen=request.user)
        except Vote.DoesNotExist:
            pass
        
        try:
            user_rating = candidate.ratings.get(citizen=request.user)
        except Rating.DoesNotExist:
            pass
    
    context = {
        "page_title": f"المرشح {candidate.name}",
        "meta_description": f"تعرف على المرشح {candidate.name} من {candidate.governorate_name} - {candidate.constituency}",
        "candidate": candidate,
        "total_votes": total_votes,
        "approve_votes": approve_votes,
        "disapprove_votes": disapprove_votes,
        "avg_rating": round(avg_rating, 1),
        "total_ratings": total_ratings,
        "rating_distribution": rating_distribution,
        "ratings": ratings[:10],  # Show first 10 ratings
        "electoral_promises": electoral_promises,
        "service_history": service_history,
        "recent_messages": recent_messages,
        "user_vote": user_vote,
        "user_rating": user_rating,
    }
    return render(request, "candidates/candidate_detail.html", context)


@login_required
@require_POST
def vote_candidate(request, pk):
    """
    التصويت لمرشح (أؤيد/أعارض)
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    vote_type = request.POST.get("vote_type")
    
    if vote_type not in ["approve", "disapprove"]:
        messages.error(request, "نوع التصويت غير صحيح.")
        return redirect("candidates:candidate_detail", pk=pk)
    
    # Check if user already voted
    existing_vote = Vote.objects.filter(candidate=candidate, citizen=request.user).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Remove vote if same type
            existing_vote.delete()
            messages.success(request, "تم إلغاء تصويتك.")
            
            # Log activity
            ActivityLog.log_activity(
                user=request.user,
                action_type="vote_removed",
                description=f"إلغاء تصويت {existing_vote.get_vote_type_display()} للمرشح {candidate.name}",
                content_object=candidate
            )
        else:
            # Update vote type
            existing_vote.vote_type = vote_type
            existing_vote.save()
            messages.success(request, f"تم تحديث تصويتك إلى \"{existing_vote.get_vote_type_display()}\".")
            
            # Log activity
            ActivityLog.log_activity(
                user=request.user,
                action_type="vote_updated",
                description=f"تحديث التصويت إلى {existing_vote.get_vote_type_display()} للمرشح {candidate.name}",
                content_object=candidate
            )
    else:
        # Create new vote
        vote = Vote.objects.create(
            candidate=candidate,
            citizen=request.user,
            vote_type=vote_type
        )
        messages.success(request, f"تم تسجيل تصويتك: \"{vote.get_vote_type_display()}\".")
        
        # Log activity
        ActivityLog.log_activity(
            user=request.user,
            action_type="vote_cast",
            description=f"تصويت {vote.get_vote_type_display()} للمرشح {candidate.name}",
            content_object=candidate
        )
    
    return redirect("candidates:candidate_detail", pk=pk)


@login_required
@require_POST
def rate_candidate(request, pk):
    """
    تقييم مرشح بالنجوم مع تعليق
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    stars = request.POST.get("stars")
    comment = request.POST.get("comment", "").strip()
    
    try:
        stars = int(stars)
        if stars < 1 or stars > 5:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "تقييم النجوم يجب أن يكون بين 1 و 5.")
        return redirect("candidates:candidate_detail", pk=pk)
    
    # Check if user already rated
    existing_rating = Rating.objects.filter(candidate=candidate, citizen=request.user).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.stars = stars
        existing_rating.comment = comment
        existing_rating.save()
        messages.success(request, "تم تحديث تقييمك بنجاح.")
        
        # Log activity
        ActivityLog.log_activity(
            user=request.user,
            action_type="rating_updated",
            description=f"تحديث تقييم {stars} نجوم للمرشح {candidate.name}",
            content_object=candidate
        )
    else:
        # Create new rating
        rating = Rating.objects.create(
            candidate=candidate,
            citizen=request.user,
            stars=stars,
            comment=comment
        )
        messages.success(request, "تم إضافة تقييمك بنجاح.")
        
        # Log activity
        ActivityLog.log_activity(
            user=request.user,
            action_type="rating_given",
            description=f"تقييم {stars} نجوم للمرشح {candidate.name}",
            content_object=candidate
        )
    
    return redirect("candidates:candidate_detail", pk=pk)


@login_required
def candidate_dashboard(request):
    """
    لوحة تحكم المرشح
    """
    # Check if user is a candidate
    try:
        candidate = request.user.candidate_profile
    except Candidate.DoesNotExist:
        messages.error(request, "ليس لديك صلاحية الوصول لهذه الصفحة.")
        return redirect("core:home")
    
    # Get statistics
    total_votes = candidate.votes.count()
    approve_votes = candidate.votes.filter(vote_type="approve").count()
    disapprove_votes = candidate.votes.filter(vote_type="disapprove").count()
    
    ratings = candidate.ratings.all()
    avg_rating = ratings.aggregate(Avg("stars"))["stars__avg"] or 0
    total_ratings = ratings.count()
    
    # Get unread messages
    unread_messages = candidate.messages.filter(is_read=False).order_by("-timestamp")
    
    # Get recent ratings
    recent_ratings = ratings.order_by("-timestamp")[:10]
    
    # Get electoral promises
    electoral_promises = candidate.electoral_promises.all().order_by("order")
    
    context = {
        "page_title": "لوحة تحكم المرشح",
        "candidate": candidate,
        "total_votes": total_votes,
        "approve_votes": approve_votes,
        "disapprove_votes": disapprove_votes,
        "avg_rating": round(avg_rating, 1),
        "total_ratings": total_ratings,
        "unread_messages": unread_messages,
        "recent_ratings": recent_ratings,
        "electoral_promises": electoral_promises,
    }
    return render(request, "candidates/candidate_dashboard.html", context)


def candidate_logout(request):
    logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect("core:home")


