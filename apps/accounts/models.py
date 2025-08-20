from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Citizen(models.Model):
    """Model representing a citizen"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="citizen_profile")
    first_name = models.CharField(max_length=100, verbose_name="الاسم الأول")
    last_name = models.CharField(max_length=100, verbose_name="الاسم الأخير")
    email = models.EmailField(unique=True, verbose_name="البريد الإلكتروني")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    governorate = models.ForeignKey("core.Governorate", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المحافظة")
    area_type = models.CharField(max_length=50, blank=True, verbose_name="نوع المنطقة")
    area_name = models.CharField(max_length=200, blank=True, verbose_name="اسم المنطقة")
    address = models.TextField(blank=True, verbose_name="عنوان المراسلات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "مواطن"
        verbose_name_plural = "المواطنون"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
