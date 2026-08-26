from django.urls import path
from . import views

app_name = 'study'

urlpatterns = [
    path('deck/<int:pk>/', views.study_deck_view, name='study_deck'),
    path('all/', views.study_deck_view, name='study_all'),
    path('card/<int:pk>/json/', views.get_card_json, name='card_json'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('summary/', views.session_summary_view, name='session_summary'),
]
