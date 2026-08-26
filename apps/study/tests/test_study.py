import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.decks.models import Deck
from apps.cards.models import Card
from apps.study.models import ReviewLog

class StudyTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='studyuser', password='password123')
        self.deck = Deck.objects.create(user=self.user, name='Biology')
        self.card = Card.objects.create(deck=self.deck, front='Mitochondria', back='Powerhouse of the cell')
        self.client.login(username='studyuser', password='password123')

    def test_submit_review_ajax(self):
        response = self.client.post(
            '/study/submit-review/',
            data=json.dumps({'card_id': self.card.id, 'rating': 3, 'duration_ms': 1200}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify card updated
        self.card.refresh_from_db()
        self.assertEqual(self.card.repetitions, 1)
        self.assertEqual(self.card.state, 'REVIEW')

        # Verify ReviewLog created
        self.assertEqual(ReviewLog.objects.filter(card=self.card, user=self.user).count(), 1)
