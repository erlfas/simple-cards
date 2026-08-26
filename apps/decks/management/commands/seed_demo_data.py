from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.decks.models import Deck
from apps.cards.models import Card

class Command(BaseCommand):
    help = 'Seeds sample flashcard decks (Spanish 101, Python Mastery, Science & Math) for immediate testing.'

    def handle(self, *args, **options):
        # Create or retrieve default user 'demo_user'
        user, created = User.objects.get_or_create(username='demo_user', defaults={'email': 'demo@example.com'})
        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user "{user.username}" with password "demo1234".'))
        else:
            self.stdout.write(f'Using existing user "{user.username}".')

        # 1. Spanish Deck
        deck_spanish, _ = Deck.objects.get_or_create(
            user=user,
            name='Spanish Essentials',
            defaults={
                'description': 'Core Spanish conversational phrases, vocabulary, and grammar basics.'
            }
        )
        spanish_cards = [
            ("¿Cómo te llamas?", "What is your name?", "Used when meeting someone", "phrases, greetings"),
            ("Mucho gusto", "Nice to meet you", "Polite response after introductions", "phrases, greetings"),
            ("¿Dónde está la biblioteca?", "Where is the library?", "Classic question", "questions, directions"),
            ("Por favor y gracias", "Please and thank you", "Essential politeness", "basics"),
            ("Tener ganas de (+ infinitive)", "To feel like doing something", "Idiomatic expression with tener", "grammar, verbs"),
            ("El desayuno", "The breakfast", "Morning meal", "food, vocabulary"),
            ("Buenas noches", "Good evening / Good night", "Evening greeting or departure", "greetings"),
            ("Lo siento mucho", "I am very sorry", "Apology phrase", "phrases"),
        ]
        for front, back, hint, tags in spanish_cards:
            Card.objects.get_or_create(deck=deck_spanish, front=front, defaults={'back': back, 'hint': hint, 'tags': tags})

        # 2. Python Mastery Deck
        deck_python, _ = Deck.objects.get_or_create(
            user=user,
            name='Python Mastery & Data Structures',
            defaults={
                'description': 'Advanced Python idioms, built-in functions, time complexities, and design patterns.'
            }
        )
        python_cards = [
            ("What is the average time complexity of looking up a key in a Python `dict`?", "**O(1)** (Constant time on average, backed by a hash table).", "Hash table lookup", "python, complexity, data-structures"),
            ("Explain the difference between `list.append(x)` and `list.extend(x)`.", "`append(x)` adds `x` as a single element.\n\n`extend(x)` iterates over `x` and appends each element individually.", "Collection modification", "python, lists"),
            ("What is a Python generator function and what keyword distinguishes it?", "A function that yields values on-demand using the `yield` keyword instead of `return`, maintaining state across iterations.", "Look for the yield keyword", "python, generators"),
            ("What is the GIL in CPython?", "**Global Interpreter Lock**: A mutex that prevents multiple native threads from executing Python bytecodes simultaneously in CPython.", "CPython concurrency limitation", "python, concurrency"),
            ("How does Python handle memory management?", "Via **reference counting** combined with a cyclic **garbage collector** to detect and clean reference cycles.", "Two main mechanisms", "python, internals"),
        ]
        for front, back, hint, tags in python_cards:
            Card.objects.get_or_create(deck=deck_python, front=front, defaults={'back': back, 'hint': hint, 'tags': tags})

        # 3. Science & Math Formulas
        deck_math, _ = Deck.objects.get_or_create(
            user=user,
            name='Physics & Math Formulas',
            defaults={
                'description': 'Fundamental mathematical equations and physics laws with LaTeX formatting.'
            }
        )
        math_cards = [
            ("What is Einstein's mass-energy equivalence equation?", "$$E = mc^2$$\n\nWhere $E$ is energy, $m$ is mass, and $c$ is the speed of light ($2.998 \\times 10^8 \\text{ m/s}$).", "Special relativity", "physics, equations"),
            ("State Euler's Identity, connecting the 5 fundamental math constants.", "$$e^{i\\pi} + 1 = 0$$\n\nConnects $e, i, \\pi, 1, 0$.", "Most beautiful equation in math", "math, complex-numbers"),
            ("What is the Quadratic Formula for roots of $ax^2 + bx + c = 0$?", "$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$", "Roots of quadratic", "math, algebra"),
            ("What is Newton's Second Law of Motion?", "$$\\vec{F} = m\\vec{a}$$\n\nForce equals mass times acceleration.", "Force and acceleration", "physics, mechanics"),
        ]
        for front, back, hint, tags in math_cards:
            Card.objects.get_or_create(deck=deck_math, front=front, defaults={'back': back, 'hint': hint, 'tags': tags})

        self.stdout.write(self.style.SUCCESS('Successfully seeded 3 demo decks with rich flashcards!'))
