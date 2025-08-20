"""
Views for messaging app
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from .models import Message
from apps.candidates.models import Candidate


@login_required
def send_message(request, candidate_id):
    """
    Send message to candidate
    """
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        content = request.POST.get('content', '').strip()
        
        if subject and content:
            message = Message.objects.create(
                candidate=candidate,
                sender_user=request.user,
                subject=subject,
                content=content
            )
            messages.success(request, 'تم إرسال الرسالة بنجاح.')
            return redirect('candidates:candidate_detail', pk=candidate_id)
        else:
            messages.error(request, 'يرجى ملء جميع الحقول المطلوبة.')
    
    context = {
        'candidate': candidate,
        'page_title': f'إرسال رسالة إلى {candidate.name}',
    }
    return render(request, 'messaging/send_message.html', context)


@login_required
def message_inbox(request):
    """
    Message inbox for users
    """
    # Get messages sent by the user
    sent_messages = Message.objects.filter(sender_user=request.user).order_by('-timestamp')
    
    context = {
        'sent_messages': sent_messages,
        'page_title': 'صندوق الرسائل',
    }
    return render(request, 'messaging/messages_management.html', context)


@login_required
def message_thread(request, message_id):
    """
    View message thread
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to view this message
    if message.sender_user != request.user and not hasattr(request.user, 'candidate_profile'):
        messages.error(request, 'ليس لديك صلاحية لعرض هذه الرسالة.')
        return redirect('messaging:message_inbox')
    
    context = {
        'message': message,
        'page_title': f'الرسالة: {message.subject}',
    }
    return render(request, 'messaging/message_thread.html', context)


@login_required
def reply_message(request, message_id):
    """
    Reply to a message
    """
    original_message = get_object_or_404(Message, id=message_id)
    
    # Check if user is the candidate who received the message
    if not hasattr(request.user, 'candidate_profile') or request.user.candidate_profile != original_message.candidate:
        messages.error(request, 'ليس لديك صلاحية للرد على هذه الرسالة.')
        return redirect('messaging:message_inbox')
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if content:
            reply = Message.objects.create(
                candidate=original_message.candidate,
                sender_user=request.user,
                subject=f'رد: {original_message.subject}',
                content=content,
                reply_to=original_message
            )
            messages.success(request, 'تم إرسال الرد بنجاح.')
            return redirect('messaging:message_thread', message_id=original_message.id)
        else:
            messages.error(request, 'يرجى كتابة محتوى الرد.')
    
    context = {
        'original_message': original_message,
        'page_title': f'الرد على: {original_message.subject}',
    }
    return render(request, 'messaging/reply_message.html', context)
