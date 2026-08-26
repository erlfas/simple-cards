from django.urls import path
from . import views

app_name = 'decks'

urlpatterns = [
    path('', views.deck_list, name='deck_list'),
    path('create/', views.deck_create, name='deck_create'),
    path('<int:pk>/', views.deck_detail, name='deck_detail'),
    path('<int:pk>/edit/', views.deck_update, name='deck_update'),
    path('<int:pk>/delete/', views.deck_delete, name='deck_delete'),
    path('<int:pk>/export/csv/', views.deck_export_csv, name='deck_export_csv'),
    path('<int:pk>/export/json/', views.deck_export_json, name='deck_export_json'),
]
