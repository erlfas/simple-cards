from django.test import TestCase
from django.contrib.auth.models import User
from django.db import connection
from apps.decks.models import Deck
from apps.cards.models import Card
from apps.core.fields import encrypt_value, decrypt_value

class EncryptionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='crypto_user', password='password123')
        self.deck = Deck.objects.create(
            user=self.user,
            name='Secret Deck',
            description='Top secret deck description'
        )

    def test_direct_encrypt_decrypt_functions(self):
        plaintext = "Confidential medical formula $H_2O$"
        ciphertext = encrypt_value(plaintext)
        
        self.assertNotEqual(plaintext, ciphertext)
        self.assertTrue(ciphertext.startswith('gAAAAA'))
        
        decrypted = decrypt_value(ciphertext)
        self.assertEqual(plaintext, decrypted)

    def test_card_field_encryption_at_rest(self):
        secret_question = "What is the secret API key?"
        secret_answer = "sk_live_998877665544332211"
        secret_hint = "Starts with sk_live"

        card = Card.objects.create(
            deck=self.deck,
            front=secret_question,
            back=secret_answer,
            hint=secret_hint,
            tags="secrets,api"
        )

        # 1. Verify that querying via raw SQL directly from the database returns ciphertext
        with connection.cursor() as cursor:
            cursor.execute("SELECT front, back, hint FROM cards_card WHERE id = %s", [card.id])
            raw_front, raw_back, raw_hint = cursor.fetchone()

        self.assertNotEqual(raw_front, secret_question)
        self.assertTrue(raw_front.startswith('gAAAAA'))
        self.assertNotEqual(raw_back, secret_answer)
        self.assertTrue(raw_back.startswith('gAAAAA'))
        self.assertNotEqual(raw_hint, secret_hint)
        self.assertTrue(raw_hint.startswith('gAAAAA'))

        # 2. Verify that reading the card via Django ORM automatically decrypts it
        fetched_card = Card.objects.get(id=card.id)
        self.assertEqual(fetched_card.front, secret_question)
        self.assertEqual(fetched_card.back, secret_answer)
        self.assertEqual(fetched_card.hint, secret_hint)
        self.assertEqual(fetched_card.tags, "secrets,api")

    def test_deck_description_encryption_at_rest(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT description FROM decks_deck WHERE id = %s", [self.deck.id])
            raw_desc, = cursor.fetchone()

        self.assertNotEqual(raw_desc, 'Top secret deck description')
        self.assertTrue(raw_desc.startswith('gAAAAA'))

        fetched_deck = Deck.objects.get(id=self.deck.id)
        self.assertEqual(fetched_deck.description, 'Top secret deck description')
