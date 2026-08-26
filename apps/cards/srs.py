"""
Spaced Repetition Engine implementing the SuperMemo-2 (SM-2) algorithm adapted for Anki-style reviews.
"""
from datetime import timedelta
from django.utils import timezone

RATING_AGAIN = 1
RATING_HARD = 2
RATING_GOOD = 3
RATING_EASY = 4

MINIMUM_EASE_FACTOR = 1.30
INITIAL_EASE_FACTOR = 2.50
MAXIMUM_EASE_FACTOR = 3.50

def calculate_next_review(card, rating: int):
    """
    Computes updated interval, ease factor, repetition count, state, and next due date
    for a flashcard given a user rating from 1 to 4.

    Ratings:
      1: Again (failed recall, reset interval, decrease ease)
      2: Hard (difficult recall, slight interval increase, decrease ease slightly)
      3: Good (standard recall, increase interval by ease factor)
      4: Easy (effortless recall, larger interval increase with bonus, increase ease)

    Returns a dict with updated values.
    """
    now = timezone.now()
    ease_factor = float(card.ease_factor)
    reps = card.repetitions
    lapses = card.lapses
    current_interval = float(card.interval_days)

    if rating == RATING_AGAIN:
        # Failure: reset progress, flag lapse, schedule review in 10 minutes (0.007 days)
        reps = 0
        lapses += 1
        interval_days = 0.007  # ~10 minutes
        ease_factor = max(MINIMUM_EASE_FACTOR, ease_factor - 0.20)
        state = 'LEARNING'
        due_date = now + timedelta(minutes=10)

    elif rating == RATING_HARD:
        # Hard: passed with difficulty
        if reps == 0:
            interval_days = 1.0
            reps = 1
        else:
            # 1.2x modifier for hard reviews
            interval_days = max(1.0, round(current_interval * 1.2, 2))
        ease_factor = max(MINIMUM_EASE_FACTOR, ease_factor - 0.15)
        state = 'REVIEW'
        due_date = now + timedelta(days=interval_days)

    elif rating == RATING_GOOD:
        # Good: normal progression
        if reps == 0:
            interval_days = 1.0
        elif reps == 1:
            interval_days = 3.0
        else:
            interval_days = round(max(1.0, current_interval * ease_factor), 2)
        reps += 1
        state = 'REVIEW'
        due_date = now + timedelta(days=interval_days)

    elif rating == RATING_EASY:
        # Easy: rapid progression with bonus
        if reps == 0:
            interval_days = 4.0
        elif reps == 1:
            interval_days = 7.0
        else:
            easy_bonus = 1.3
            interval_days = round(max(2.0, current_interval * ease_factor * easy_bonus), 2)
        reps += 1
        ease_factor = min(MAXIMUM_EASE_FACTOR, ease_factor + 0.15)
        state = 'REVIEW'
        due_date = now + timedelta(days=interval_days)

    else:
        raise ValueError(f"Invalid rating: {rating}. Must be between 1 and 4.")

    return {
        'ease_factor': round(ease_factor, 2),
        'interval_days': round(interval_days, 3),
        'repetitions': reps,
        'lapses': lapses,
        'state': state,
        'due_date': due_date,
        'last_reviewed_at': now,
    }


def preview_intervals(card):
    """
    Returns a human-readable preview of the interval changes for each button:
    Again, Hard, Good, Easy.
    """
    def format_interval(days):
        if days < 0.05:
            return "10m"
        elif days < 1:
            hours = int(days * 24)
            return f"{hours}h"
        elif days < 30:
            return f"{int(round(days))}d"
        elif days < 365:
            months = round(days / 30.4, 1)
            return f"{months}mo"
        else:
            years = round(days / 365.25, 1)
            return f"{years}y"

    return {
        1: format_interval(calculate_next_review(card, 1)['interval_days']),
        2: format_interval(calculate_next_review(card, 2)['interval_days']),
        3: format_interval(calculate_next_review(card, 3)['interval_days']),
        4: format_interval(calculate_next_review(card, 4)['interval_days']),
    }
