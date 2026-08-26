from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_new_cards_limit', 'daily_review_limit', 'streak_days', 'last_studied_date')
    search_fields = ('user__username', 'user__email')
