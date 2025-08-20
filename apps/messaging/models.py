from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Message(models.Model):
    """Model representing messages from citizens to candidates"""
    candidate = models.ForeignKey('candidates.Candidate', on_delete=models.CASCADE, related_name='messages')
    sender_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المرسل المسجل")
    sender_name = models.CharField(max_length=200, verbose_name="اسم المرسل", blank=True)
    sender_email = models.EmailField(verbose_name="بريد المرسل", blank=True)
    subject = models.CharField(max_length=300, verbose_name="موضوع الرسالة")
    content = models.TextField(verbose_name="محتوى الرسالة")
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True, verbose_name="مرفق")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت الإرسال")
    is_read = models.BooleanField(default=False, verbose_name="مقروءة")
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        verbose_name = "رسالة"
        verbose_name_plural = "الرسائل"
        ordering = ['-timestamp']

    def __str__(self):
        sender = self.sender_user.get_full_name() if self.sender_user else self.sender_name
        return f"رسالة من {sender} إلى {self.candidate.name}"
