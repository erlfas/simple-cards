from django.contrib import admin
from .models import Deck

@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'total_cards', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'user__username')
