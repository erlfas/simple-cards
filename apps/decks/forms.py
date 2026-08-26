from django import forms
from .models import Deck

class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 border border-neutral-300 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-sm',
                'placeholder': 'e.g. Spanish Vocabulary, Python Concepts'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 border border-neutral-300 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-sm',
                'rows': 3,
                'placeholder': 'Description or study goals for this deck (optional)'
            }),
        }
