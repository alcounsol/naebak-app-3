from django.contrib import admin
from .models import (
    Candidate,
    ElectoralPromise,
    PublicServiceHistory,
    Message,
    Rating,
    RatingReply,
    Vote,
    News,
    ActivityLog,
)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'governorate_name', 'constituency', 'is_featured', 'created_at')
    search_fields = ('name', 'role', 'constituency', 'user__username', 'election_symbol', 'election_number')
    list_filter = ('role', 'governorate_id', 'is_featured', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    def governorate_name(self, obj):
        return obj.governorate_name
    governorate_name.short_description = 'المحافظة'


@admin.register(ElectoralPromise)
class ElectoralPromiseAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'title', 'order', 'created_at')
    search_fields = ('title', 'description', 'candidate__name')
    list_filter = ('candidate', 'created_at')
    ordering = ('candidate', 'order')


@admin.register(PublicServiceHistory)
class PublicServiceHistoryAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'position', 'start_year', 'end_year')
    search_fields = ('position', 'description', 'candidate__name')
    list_filter = ('candidate', 'start_year', 'end_year')
    ordering = ('candidate', '-start_year')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'sender_name', 'subject', 'timestamp', 'is_read')
    search_fields = ('subject', 'content', 'sender_name', 'sender_email')
    list_filter = ('candidate', 'is_read', 'timestamp')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'citizen', 'stars', 'timestamp', 'is_read')
    search_fields = ('comment', 'candidate__name', 'citizen__username')
    list_filter = ('candidate', 'stars', 'is_read', 'timestamp')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(RatingReply)
class RatingReplyAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'rating', 'timestamp')
    search_fields = ('content', 'candidate__name')
    list_filter = ('candidate', 'timestamp')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'citizen', 'vote_type', 'timestamp')
    search_fields = ('candidate__name', 'citizen__username')
    list_filter = ('candidate', 'vote_type', 'timestamp')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'author', 'publish_date', 'views_count')
    search_fields = ('title', 'content', 'tags')
    list_filter = ('status', 'priority', 'author', 'publish_date', 'show_on_homepage', 'show_on_ticker')
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    ordering = ('-publish_date', '-created_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'severity', 'timestamp', 'ip_address')
    search_fields = ('description', 'user__username', 'ip_address')
    list_filter = ('action_type', 'severity', 'timestamp')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of activity logs
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing of activity logs

