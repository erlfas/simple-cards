from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from apps.decks.models import Deck
from apps.cards.models import Card

class DeckTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='deckuser', password='password123')
        self.deck = Deck.objects.create(user=self.user, name='Geography')

    def test_deck_counts(self):
        Card.objects.create(deck=self.deck, front='Q1', back='A1', state='NEW')
        Card.objects.create(deck=self.deck, front='Q2', back='A2', state='LEARNING')
        Card.objects.create(deck=self.deck, front='Q3', back='A3', state='REVIEW')

        self.assertEqual(self.deck.total_cards, 3)
        self.assertEqual(self.deck.new_cards_count, 1)
        self.assertEqual(self.deck.learning_cards_count, 1)

    def test_deck_unique_per_user(self):
        with self.assertRaises(IntegrityError):
            Deck.objects.create(user=self.user, name='Geography')
