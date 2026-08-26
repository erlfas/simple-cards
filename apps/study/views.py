import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.utils import timezone
from apps.decks.models import Deck
from apps.cards.models import Card
from apps.cards.srs import calculate_next_review, preview_intervals
from .models import ReviewLog

def update_user_streak(user):
    profile = user.profile
    today = date.today()
    if profile.last_studied_date is None:
        profile.streak_days = 1
        profile.last_studied_date = today
        profile.save()
    elif profile.last_studied_date == today:
        # Already studied today, keep streak
        pass
    elif profile.last_studied_date == today - timedelta(days=1):
        # Studied yesterday, increment streak
        profile.streak_days += 1
        profile.last_studied_date = today
        profile.save()
    else:
        # Missed days, reset streak to 1
        profile.streak_days = 1
        profile.last_studied_date = today
        profile.save()

@login_required
def study_deck_view(request, pk=None):
    now = timezone.now()
    profile = request.user.profile
    
    if pk:
        deck = get_object_or_404(Deck, pk=pk, user=request.user)
        deck_cards = deck.cards.all()
    else:
        deck = None
        deck_cards = Card.objects.filter(deck__user=request.user)

    # Filter due review cards + learning cards
    due_cards = deck_cards.filter(state__in=['LEARNING', 'REVIEW'], due_date__lte=now)
    
    # Filter new cards limited by user profile daily limit
    new_cards = deck_cards.filter(state='NEW')[:profile.daily_new_cards_limit]

    # Combine cards for the session
    session_cards = list(due_cards) + list(new_cards)

    if not session_cards:
        return render(request, 'study/study_empty.html', {
            'deck': deck,
            'total_in_deck': deck.total_cards if deck else deck_cards.count(),
        })

    # Prepare first card data and card queue IDs
    card_ids = [c.id for c in session_cards]
    first_card = session_cards[0]
    
    context = {
        'deck': deck,
        'card_ids_json': json.dumps(card_ids),
        'initial_card': first_card,
        'initial_intervals': preview_intervals(first_card),
        'total_cards': len(card_ids),
    }
    return render(request, 'study/study_session.html', context)


@login_required
def get_card_json(request, pk):
    card = get_object_or_404(Card, pk=pk, deck__user=request.user)
    return JsonResponse({
        'id': card.id,
        'deck_name': card.deck.name,
        'front': card.rendered_front,
        'back': card.rendered_back,
        'hint': card.hint,
        'state': card.state,
        'intervals': preview_intervals(card),
    })


@login_required
@require_POST
def submit_review(request):
    try:
        data = json.loads(request.body)
        card_id = int(data.get('card_id'))
        rating = int(data.get('rating'))
        duration_ms = int(data.get('duration_ms', 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid payload")

    card = get_object_or_404(Card, id=card_id, deck__user=request.user)
    
    if rating not in [1, 2, 3, 4]:
        return HttpResponseBadRequest("Rating must be 1, 2, 3, or 4")

    # Record previous values for logging
    prev_interval = card.interval_days
    prev_ease = card.ease_factor

    # Calculate SM-2 update
    update_data = calculate_next_review(card, rating)

    # Update Card
    card.ease_factor = update_data['ease_factor']
    card.interval_days = update_data['interval_days']
    card.repetitions = update_data['repetitions']
    card.lapses = update_data['lapses']
    card.state = update_data['state']
    card.due_date = update_data['due_date']
    card.last_reviewed_at = update_data['last_reviewed_at']
    card.save()

    # Log Review
    ReviewLog.objects.create(
        user=request.user,
        card=card,
        rating=rating,
        duration_ms=duration_ms,
        prev_interval=prev_interval,
        new_interval=card.interval_days,
        prev_ease=prev_ease,
        new_ease=card.ease_factor,
    )

    # Update user streak
    update_user_streak(request.user)

    return JsonResponse({
        'success': True,
        'card_id': card.id,
        'rating': rating,
        'new_interval': str(card.interval_days),
        'new_state': card.state,
        'due_date': card.due_date.isoformat(),
    })


@login_required
def session_summary_view(request):
    return render(request, 'study/session_summary.html')
