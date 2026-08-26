import json
from datetime import date, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from apps.study.models import ReviewLog
from apps.cards.models import Card
from apps.decks.models import Deck

@login_required
def analytics_dashboard(request):
    user = request.user
    now = timezone.now()
    today = timezone.localdate()

    # Total stats
    total_reviews = ReviewLog.objects.filter(user=user).count()
    successful_reviews = ReviewLog.objects.filter(user=user, rating__in=[3, 4]).count()
    retention_rate = round((successful_reviews / total_reviews * 100), 1) if total_reviews > 0 else 0

    # Total cards breakdown
    user_cards = Card.objects.filter(deck__user=user)
    total_cards = user_cards.count()
    new_cards = user_cards.filter(state='NEW').count()
    learning_cards = user_cards.filter(state='LEARNING').count()
    review_cards = user_cards.filter(state='REVIEW').count()

    # Rating distribution
    rating_counts = {
        'again': ReviewLog.objects.filter(user=user, rating=1).count(),
        'hard': ReviewLog.objects.filter(user=user, rating=2).count(),
        'good': ReviewLog.objects.filter(user=user, rating=3).count(),
        'easy': ReviewLog.objects.filter(user=user, rating=4).count(),
    }

    # Daily activity for the past 90 days (Heatmap data)
    start_date = today - timedelta(days=89)
    daily_logs = (
        ReviewLog.objects.filter(user=user, reviewed_at__date__gte=start_date)
        .values('reviewed_at__date')
        .annotate(count=Count('id'))
        .order_by('reviewed_at__date')
    )
    daily_activity_map = {item['reviewed_at__date'].strftime('%Y-%m-%d'): item['count'] for item in daily_logs}

    # Generate full 90-day grid with counts and intensity levels (0 to 4)
    heatmap_days = []
    for i in range(90):
        current_d = start_date + timedelta(days=i)
        d_str = current_d.strftime('%Y-%m-%d')
        count = daily_activity_map.get(d_str, 0)
        if count == 0:
            level = 0
        elif count <= 5:
            level = 1
        elif count <= 15:
            level = 2
        elif count <= 30:
            level = 3
        else:
            level = 4
        
        heatmap_days.append({
            'date': d_str,
            'weekday': current_d.strftime('%a'),
            'count': count,
            'level': level,
        })

    # Forecast of due cards for next 14 days
    forecast_days = []
    for i in range(14):
        target_date = today + timedelta(days=i)
        count = user_cards.filter(due_date__date=target_date, state__in=['LEARNING', 'REVIEW']).count()
        forecast_days.append({
            'date': target_date.strftime('%b %d'),
            'count': count,
        })

    context = {
        'total_reviews': total_reviews,
        'retention_rate': retention_rate,
        'total_cards': total_cards,
        'new_cards': new_cards,
        'learning_cards': learning_cards,
        'review_cards': review_cards,
        'rating_counts': rating_counts,
        'rating_counts_json': json.dumps(rating_counts),
        'heatmap_days': heatmap_days,
        'forecast_days': forecast_days,
        'forecast_days_json': json.dumps(forecast_days),
        'streak_days': user.profile.streak_days,
    }
    return render(request, 'analytics/dashboard.html', context)
