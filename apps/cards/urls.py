from django.urls import path
from . import views

app_name = 'cards'

urlpatterns = [
    path('', views.card_list, name='card_list'),
    path('create/', views.card_create, name='card_create'),
    path('<int:pk>/edit/', views.card_update, name='card_update'),
    path('<int:pk>/delete/', views.card_delete, name='card_delete'),
    path('bulk-create/', views.bulk_create_cards, name='bulk_create'),
]
