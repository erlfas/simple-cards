from django.test import TestCase
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile

class AccountsTestCase(TestCase):
    def test_user_profile_signal(self):
        user = User.objects.create_user(username='profileuser', password='password123')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.daily_new_cards_limit, 20)
        self.assertEqual(user.profile.streak_days, 0)
