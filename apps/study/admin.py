from django.contrib import admin
from .models import ReviewLog

@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'card', 'rating', 'prev_interval', 'new_interval', 'reviewed_at')
    list_filter = ('rating', 'reviewed_at', 'user')
    search_fields = ('user__username', 'card__front')
