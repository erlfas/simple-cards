from django import forms
from .models import Card
from apps.decks.models import Deck

class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ('deck', 'front', 'back', 'hint', 'tags')
        widgets = {
            'deck': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700'}),
            'front': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700 font-mono text-sm', 'rows': 4, 'placeholder': 'Question / Prompt (Supports Markdown & $E=mc^2$)'}),
            'back': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700 font-mono text-sm', 'rows': 4, 'placeholder': 'Answer / Solution / Explanation'}),
            'hint': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700', 'placeholder': 'Optional hint'}),
            'tags': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700', 'placeholder': 'e.g. grammar, vocabulary, unit1'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['deck'].queryset = Deck.objects.filter(user=user)


class BulkCardCreateForm(forms.Form):
    deck = forms.ModelChoiceField(
        queryset=Deck.objects.none(),
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700'})
    )
    separator = forms.ChoiceField(
        choices=[('tab', 'Tab separated (TSV)'), ('comma', 'Comma separated (CSV)'), ('semicolon', 'Semicolon (;)')],
        initial='tab',
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700'})
    )
    raw_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700 font-mono text-sm',
            'rows': 10,
            'placeholder': 'Front\tBack\tHint (optional)\nBonjour\tHello\tGreeting\nGracias\tThank you\tCourtesy'
        }),
        help_text="Paste your cards line by line. Each line should contain Front, Back, and optionally Hint separated by your chosen separator."
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['deck'].queryset = Deck.objects.filter(user=user)
