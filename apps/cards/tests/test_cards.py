from django.test import TestCase
from django.contrib.auth.models import User
from apps.decks.models import Deck
from apps.cards.models import Card
from apps.cards.srs import calculate_next_review, preview_intervals, RATING_AGAIN, RATING_HARD, RATING_GOOD, RATING_EASY

class SRSTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')
        self.card = Card.objects.create(
            deck=self.deck,
            front='Question 1',
            back='Answer 1',
            ease_factor=2.50,
            interval_days=0.0,
            repetitions=0
        )

    def test_first_good_review(self):
        result = calculate_next_review(self.card, RATING_GOOD)
        self.assertEqual(result['interval_days'], 1.0)
        self.assertEqual(result['repetitions'], 1)
        self.assertEqual(result['state'], 'REVIEW')
        self.assertEqual(result['ease_factor'], 2.50)

    def test_first_easy_review(self):
        result = calculate_next_review(self.card, RATING_EASY)
        self.assertEqual(result['interval_days'], 4.0)
        self.assertEqual(result['repetitions'], 1)
        self.assertEqual(result['state'], 'REVIEW')
        self.assertEqual(result['ease_factor'], 2.65)

    def test_again_review_resets_reps(self):
        self.card.repetitions = 5
        self.card.interval_days = 20.0
        self.card.ease_factor = 2.50
        result = calculate_next_review(self.card, RATING_AGAIN)
        self.assertEqual(result['repetitions'], 0)
        self.assertEqual(result['lapses'], 1)
        self.assertEqual(result['state'], 'LEARNING')
        self.assertEqual(result['ease_factor'], 2.30)
        self.assertLess(result['interval_days'], 0.1)

    def test_markdown_and_math_rendering(self):
        card = Card.objects.create(
            deck=self.deck,
            front='What is **bold** and $E=mc^2$?',
            back='It is `code` and $$x^2+y^2=z^2$$'
        )
        self.assertIn('<strong>bold</strong>', card.rendered_front)
        self.assertIn('<code>code</code>', card.rendered_back)
        self.assertIn('$E=mc^2$', card.rendered_front)

    def test_preview_intervals(self):
        previews = preview_intervals(self.card)
        self.assertIn(1, previews)
        self.assertIn(2, previews)
        self.assertIn(3, previews)
        self.assertIn(4, previews)
