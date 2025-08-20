from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Rating(models.Model):
    """Model representing ratings and comments from citizens"""
    candidate = models.ForeignKey('candidates.Candidate', on_delete=models.CASCADE, related_name='ratings')
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المواطن")
    stars = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="التقييم بالنجوم")
    comment = models.TextField(verbose_name="التعليق", blank=True)
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت التقييم")
    is_read = models.BooleanField(default=False, verbose_name="مقروء")

    class Meta:
        verbose_name = "تقييم"
        verbose_name_plural = "التقييمات"
        ordering = ['-timestamp']
        unique_together = ['candidate', 'citizen']  # One rating per citizen per candidate

    def __str__(self):
        return f"تقييم {self.stars} نجوم من {self.citizen.get_full_name()} للمرشح {self.candidate.name}"


class RatingReply(models.Model):
    """Model representing replies to ratings from candidates"""
    rating = models.OneToOneField(Rating, on_delete=models.CASCADE, related_name='reply')
    candidate = models.ForeignKey('candidates.Candidate', on_delete=models.CASCADE)
    content = models.TextField(verbose_name="رد المرشح")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت الرد")

    class Meta:
        verbose_name = "رد على تقييم"
        verbose_name_plural = "الردود على التقييمات"

    def __str__(self):
        return f"رد {self.candidate.name} على تقييم {self.rating.citizen.get_full_name()}"


class Vote(models.Model):
    """Model representing votes (approve/disapprove) for candidates"""
    VOTE_CHOICES = [
        ('approve', 'أؤيد'),
        ('disapprove', 'أعارض'),
    ]
    
    candidate = models.ForeignKey('candidates.Candidate', on_delete=models.CASCADE, related_name='votes')
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="المواطن")
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES, verbose_name="نوع التصويت")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="وقت التصويت")

    class Meta:
        verbose_name = "تصويت"
        verbose_name_plural = "التصويتات"
        ordering = ['-timestamp']
        unique_together = ['candidate', 'citizen']  # One vote per citizen per candidate

    def __str__(self):
        return f"{self.get_vote_type_display()} من {self.citizen.get_full_name()} للمرشح {self.candidate.name}"
