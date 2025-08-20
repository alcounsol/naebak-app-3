from django.contrib import admin
from .models import (
    Governorate,
    ActivityLog,
)


@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'severity', 'timestamp')
    search_fields = ('description', 'user__username', 'ip_address')
    list_filter = ('action_type', 'severity', 'timestamp')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        # Prevent manual addition of activity logs
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing of activity logs
        return False

