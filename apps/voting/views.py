"""
Views for voting app
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from .models import Rating, Vote
from apps.candidates.models import Candidate


def rating_list(request):
    """
    List all ratings
    """
    ratings = Rating.objects.all().order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(ratings, 20)  # Show 20 ratings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'التقييمات',
        'page_obj': page_obj,
    }
    return render(request, 'voting/rating_list.html', context)


def vote_list(request):
    """
    List all votes
    """
    votes = Vote.objects.all().order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(votes, 20)  # Show 20 votes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'التصويتات',
        'page_obj': page_obj,
    }
    return render(request, 'voting/vote_list.html', context)


@login_required
@require_POST
def api_vote(request):
    """
    API endpoint for voting
    """
    candidate_id = request.POST.get('candidate_id')
    vote_type = request.POST.get('vote_type')
    
    if not candidate_id or vote_type not in ['approve', 'disapprove']:
        return JsonResponse({'success': False, 'error': 'Invalid data'})
    
    try:
        candidate = Candidate.objects.get(id=candidate_id)
        
        # Check if user already voted
        existing_vote = Vote.objects.filter(candidate=candidate, citizen=request.user).first()
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Remove vote if same type
                existing_vote.delete()
                return JsonResponse({'success': True, 'action': 'removed'})
            else:
                # Update vote type
                existing_vote.vote_type = vote_type
                existing_vote.save()
                return JsonResponse({'success': True, 'action': 'updated'})
        else:
            # Create new vote
            Vote.objects.create(
                candidate=candidate,
                citizen=request.user,
                vote_type=vote_type
            )
            return JsonResponse({'success': True, 'action': 'created'})
            
    except Candidate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Candidate not found'})


@login_required
@require_POST
def api_rate(request):
    """
    API endpoint for rating
    """
    candidate_id = request.POST.get('candidate_id')
    stars = request.POST.get('stars')
    comment = request.POST.get('comment', '').strip()
    
    try:
        stars = int(stars)
        if stars < 1 or stars > 5:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid rating'})
    
    try:
        candidate = Candidate.objects.get(id=candidate_id)
        
        # Check if user already rated
        existing_rating = Rating.objects.filter(candidate=candidate, citizen=request.user).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.stars = stars
            existing_rating.comment = comment
            existing_rating.save()
            return JsonResponse({'success': True, 'action': 'updated'})
        else:
            # Create new rating
            Rating.objects.create(
                candidate=candidate,
                citizen=request.user,
                stars=stars,
                comment=comment
            )
            return JsonResponse({'success': True, 'action': 'created'})
            
    except Candidate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Candidate not found'})
