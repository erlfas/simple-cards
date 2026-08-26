from django.contrib import admin
from .models import Card

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('front_snippet', 'deck', 'state', 'ease_factor', 'interval_days', 'repetitions', 'due_date')
    list_filter = ('state', 'deck__user', 'deck')
    search_fields = ('front', 'back', 'tags')

    def front_snippet(self, obj):
        return (obj.front[:50] + '...') if len(obj.front) > 50 else obj.front
    front_snippet.short_description = 'Front'
