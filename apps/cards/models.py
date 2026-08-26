import markdown
import bleach
from django.db import models
from django.utils import timezone
from apps.decks.models import Deck
from apps.core.fields import EncryptedTextField, EncryptedCharField

class Card(models.Model):
    STATE_CHOICES = [
        ('NEW', 'New'),
        ('LEARNING', 'Learning'),
        ('REVIEW', 'Review'),
        ('SUSPENDED', 'Suspended'),
    ]

    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='cards')
    
    # Encrypted fields for maximum privacy (AES-128-CBC + HMAC-SHA256 at rest)
    front = EncryptedTextField(help_text="Question / Prompt (Encrypted at rest)")
    back = EncryptedTextField(help_text="Answer / Solution (Encrypted at rest)")
    hint = EncryptedCharField(max_length=255, blank=True, help_text="Optional hint (Encrypted at rest)")
    tags = EncryptedCharField(max_length=255, blank=True, help_text="Comma-separated tags (Encrypted at rest)")

    # Spaced Repetition (SM-2) tracking
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='NEW')
    ease_factor = models.DecimalField(max_digits=4, decimal_places=2, default=2.50)
    interval_days = models.DecimalField(max_digits=8, decimal_places=3, default=0.000)
    repetitions = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)
    
    due_date = models.DateTimeField(default=timezone.now)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'created_at']

    def __str__(self):
        snippet = (self.front[:50] + '...') if len(self.front) > 50 else self.front
        return f"[{self.deck.name}] {snippet}"

    @property
    def is_due(self):
        return self.due_date <= timezone.now()

    @property
    def rendered_front(self):
        return self._render_markdown(self.front)

    @property
    def rendered_back(self):
        return self._render_markdown(self.back)

    def _render_markdown(self, text):
        if not text:
            return ""
        html = markdown.markdown(text, extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists'])
        allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({
            'p', 'pre', 'code', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'br', 'span', 'div', 'img', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        })
        allowed_attrs = {
            **bleach.sanitizer.ALLOWED_ATTRIBUTES,
            '*': ['class', 'id', 'style'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        }
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
