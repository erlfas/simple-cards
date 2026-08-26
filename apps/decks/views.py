import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from .models import Deck
from .forms import DeckForm
from apps.cards.models import Card

@login_required
def deck_list(request):
    query = request.GET.get('q', '').strip().lower()
    decks_qs = Deck.objects.filter(user=request.user)

    if query:
        # Filter on unencrypted name or decrypted description in memory
        decks = [d for d in decks_qs if query in d.name.lower() or (d.description and query in d.description.lower())]
    else:
        decks = list(decks_qs)

    total_cards = sum(d.total_cards for d in decks)
    total_due = sum(d.due_cards_count for d in decks)
    total_new = sum(d.new_cards_count for d in decks)

    context = {
        'decks': decks,
        'query': query,
        'total_cards': total_cards,
        'total_due': total_due,
        'total_new': total_new,
    }
    return render(request, 'decks/deck_list.html', context)


@login_required
def deck_detail(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    cards_qs = deck.cards.all()

    query = request.GET.get('q', '').strip().lower()
    state_filter = request.GET.get('state', '').strip()

    if state_filter and state_filter in ['NEW', 'LEARNING', 'REVIEW', 'SUSPENDED']:
        cards_qs = cards_qs.filter(state=state_filter)

    if query:
        cards = [
            c for c in cards_qs
            if query in c.front.lower() or query in c.back.lower() or (c.tags and query in c.tags.lower())
        ]
    else:
        cards = list(cards_qs)

    context = {
        'deck': deck,
        'cards': cards,
        'query': query,
        'state_filter': state_filter,
    }
    return render(request, 'decks/deck_detail.html', context)


@login_required
def deck_create(request):
    if request.method == 'POST':
        form = DeckForm(request.POST)
        if form.is_valid():
            deck = form.save(commit=False)
            deck.user = request.user
            deck.save()
            messages.success(request, f'Deck "{deck.name}" created.')
            return redirect('decks:deck_detail', pk=deck.pk)
    else:
        form = DeckForm()
    return render(request, 'decks/deck_form.html', {'form': form, 'title': 'Create Deck'})


@login_required
def deck_update(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    if request.method == 'POST':
        form = DeckForm(request.POST, instance=deck)
        if form.is_valid():
            form.save()
            messages.success(request, f'Deck "{deck.name}" updated.')
            return redirect('decks:deck_detail', pk=deck.pk)
    else:
        form = DeckForm(instance=deck)
    return render(request, 'decks/deck_form.html', {'form': form, 'title': 'Edit Deck', 'deck': deck})


@login_required
def deck_delete(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    if request.method == 'POST':
        name = deck.name
        deck.delete()
        messages.success(request, f'Deck "{name}" deleted.')
        return redirect('decks:deck_list')
    return render(request, 'decks/deck_confirm_delete.html', {'deck': deck})


@login_required
def deck_export_csv(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{deck.name.replace(" ", "_")}_cards.csv"'

    writer = csv.writer(response)
    writer.writerow(['Front', 'Back', 'Hint', 'Tags', 'State', 'EaseFactor', 'IntervalDays', 'Repetitions'])
    for card in deck.cards.all():
        writer.writerow([card.front, card.back, card.hint, card.tags, card.state, card.ease_factor, card.interval_days, card.repetitions])

    return response


@login_required
def deck_export_json(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    data = {
        'deck_name': deck.name,
        'description': deck.description,
        'cards': [
            {
                'front': card.front,
                'back': card.back,
                'hint': card.hint,
                'tags': card.tags,
                'state': card.state,
                'ease_factor': str(card.ease_factor),
                'interval_days': str(card.interval_days),
                'repetitions': card.repetitions,
            }
            for card in deck.cards.all()
        ]
    }
    response = JsonResponse(data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="{deck.name.replace(" ", "_")}.json"'
    return response
