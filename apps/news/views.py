"""
Views for news app
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import News


def news_list(request):
    """
    List all published news
    """
    news_items = News.objects.filter(is_published=True).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(news_items, 10)  # Show 10 news per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'الأخبار',
        'page_obj': page_obj,
    }
    return render(request, 'news/news_list.html', context)


def news_detail(request, pk):
    """
    Display news detail
    """
    news_item = get_object_or_404(News, pk=pk, is_published=True)
    
    context = {
        'page_title': news_item.title,
        'news_item': news_item,
    }
    return render(request, 'news/news_detail.html', context)


def api_ticker_news(request):
    """
    API endpoint for ticker news
    """
    ticker_news = News.get_ticker_news()[:5]
    
    news_data = []
    for news in ticker_news:
        news_data.append({
            'id': news.id,
            'title': news.title,
            'summary': news.summary,
            'created_at': news.created_at.isoformat(),
        })
    
    return JsonResponse({'news': news_data})
