from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('decks:deck_list') if request.user.is_authenticated else redirect('accounts:login'), name='home'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('decks/', include('apps.decks.urls', namespace='decks')),
    path('cards/', include('apps.cards.urls', namespace='cards')),
    path('study/', include('apps.study.urls', namespace='study')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
]
