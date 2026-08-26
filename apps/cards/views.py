import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Card
from .forms import CardForm, BulkCardCreateForm
from apps.decks.models import Deck

@login_required
def card_list(request):
    deck_id = request.GET.get('deck')
    search_query = request.GET.get('q', '').strip().lower()
    state_filter = request.GET.get('state', '').strip()

    cards_qs = Card.objects.filter(deck__user=request.user)

    if deck_id:
        cards_qs = cards_qs.filter(deck_id=deck_id)
    if state_filter and state_filter in ['NEW', 'LEARNING', 'REVIEW', 'SUSPENDED']:
        cards_qs = cards_qs.filter(state=state_filter)

    if search_query:
        # In-memory search over decrypted front, back, and tags
        cards = [
            c for c in cards_qs
            if search_query in c.front.lower() or search_query in c.back.lower() or (c.tags and search_query in c.tags.lower())
        ]
    else:
        cards = list(cards_qs)

    paginator = Paginator(cards, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    decks = Deck.objects.filter(user=request.user)

    context = {
        'page_obj': page_obj,
        'decks': decks,
        'selected_deck': int(deck_id) if deck_id and deck_id.isdigit() else None,
        'search_query': search_query,
        'state_filter': state_filter,
    }
    return render(request, 'cards/card_list.html', context)


@login_required
def card_create(request):
    initial_deck_id = request.GET.get('deck')
    initial_deck = None
    if initial_deck_id:
        initial_deck = get_object_or_404(Deck, id=initial_deck_id, user=request.user)

    if request.method == 'POST':
        form = CardForm(request.POST, user=request.user)
        if form.is_valid():
            card = form.save(commit=False)
            if card.deck.user != request.user:
                messages.error(request, "Permission denied.")
                return redirect('decks:deck_list')
            card.save()
            messages.success(request, "Flashcard created successfully!")
            if 'save_and_add_another' in request.POST:
                return redirect(f"{request.path}?deck={card.deck.id}")
            return redirect('decks:deck_detail', pk=card.deck.id)
    else:
        form = CardForm(user=request.user, initial={'deck': initial_deck} if initial_deck else {})

    return render(request, 'cards/card_form.html', {'form': form, 'title': 'Create Flashcard', 'initial_deck': initial_deck})


@login_required
def card_update(request, pk):
    card = get_object_or_404(Card, pk=pk, deck__user=request.user)
    if request.method == 'POST':
        form = CardForm(request.POST, instance=card, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Flashcard updated.")
            return redirect('decks:deck_detail', pk=card.deck.id)
    else:
        form = CardForm(instance=card, user=request.user)
    return render(request, 'cards/card_form.html', {'form': form, 'title': 'Edit Flashcard', 'card': card})


@login_required
def card_delete(request, pk):
    card = get_object_or_404(Card, pk=pk, deck__user=request.user)
    deck_id = card.deck.id
    if request.method == 'POST':
        card.delete()
        messages.success(request, "Flashcard deleted.")
        return redirect('decks:deck_detail', pk=deck_id)
    return render(request, 'cards/card_confirm_delete.html', {'card': card})


@login_required
def bulk_create_cards(request):
    if request.method == 'POST':
        form = BulkCardCreateForm(request.POST, user=request.user)
        if form.is_valid():
            deck = form.cleaned_data['deck']
            separator_type = form.cleaned_data['separator']
            raw_data = form.cleaned_data['raw_data']

            sep_char = '\t' if separator_type == 'tab' else (',' if separator_type == 'comma' else ';')
            
            created_count = 0
            lines = raw_data.strip().splitlines()
            for line in lines:
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(sep_char)]
                if len(parts) >= 2:
                    front = parts[0]
                    back = parts[1]
                    hint = parts[2] if len(parts) >= 3 else ''
                    tags = parts[3] if len(parts) >= 4 else ''
                    if front and back:
                        Card.objects.create(
                            deck=deck,
                            front=front,
                            back=back,
                            hint=hint,
                            tags=tags,
                        )
                        created_count += 1

            messages.success(request, f"Successfully imported {created_count} flashcards into {deck.name}!")
            return redirect('decks:deck_detail', pk=deck.id)
    else:
        initial_deck = request.GET.get('deck')
        form = BulkCardCreateForm(user=request.user, initial={'deck': initial_deck} if initial_deck else {})

    return render(request, 'cards/bulk_create.html', {'form': form})
