from django.db import models
from django.contrib.auth.models import User
from apps.cards.models import Card

class ReviewLog(models.Model):
    RATING_CHOICES = [
        (1, 'Again'),
        (2, 'Hard'),
        (3, 'Good'),
        (4, 'Easy'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_logs')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='review_logs')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    duration_ms = models.PositiveIntegerField(default=0, help_text="Time taken to answer in milliseconds")
    
    prev_interval = models.DecimalField(max_digits=8, decimal_places=3)
    new_interval = models.DecimalField(max_digits=8, decimal_places=3)
    prev_ease = models.DecimalField(max_digits=4, decimal_places=2)
    new_ease = models.DecimalField(max_digits=4, decimal_places=2)

    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reviewed_at']

    def __str__(self):
        return f"{self.user.username} - Card #{self.card.id} - Rating {self.get_rating_display()} ({self.reviewed_at.strftime('%Y-%m-%d %H:%M')})"
