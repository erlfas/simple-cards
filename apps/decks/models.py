from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.core.fields import EncryptedTextField

class Deck(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='decks')
    name = models.CharField(max_length=150)
    description = EncryptedTextField(blank=True, help_text="Deck description (Encrypted at rest)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def total_cards(self):
        return self.cards.count()

    @property
    def new_cards_count(self):
        return self.cards.filter(state='NEW').count()

    @property
    def learning_cards_count(self):
        return self.cards.filter(state='LEARNING').count()

    @property
    def due_cards_count(self):
        now = timezone.now()
        return self.cards.filter(state__in=['LEARNING', 'REVIEW'], due_date__lte=now).count()

    @property
    def ready_to_study_count(self):
        """Cards ready to study: new cards + due cards."""
        return self.new_cards_count + self.due_cards_count
