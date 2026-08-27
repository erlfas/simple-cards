# 🗂️ Simple Flashcards - Minimalist Spaced Repetition

A clean, minimalist black-and-white flashcard application with Anki-inspired Spaced Repetition (SM-2), built with **Python**, **Django 5**, and **PostgreSQL**.

---

## 🌟 Key Features

1. **Clean, Minimalist Black & White Design**:
   - High-contrast, distraction-free monochrome interface.
   - Clean typography and focus on cards and content.

2. **Authentication & User Profiles**:
   - Secure registration, login, logout, and profile configuration.
   - User-specific daily limits (*Max new cards per day*, *Max reviews per day*).
   - Daily study streak tracking.

3. **Decks & Organization**:
   - Create, edit, search, export (CSV/JSON), and delete custom decks.
   - Live card counts: *New*, *Learning*, and *Due for Review*.

4. **Card Browser & Rich Editor**:
   - **Markdown & LaTeX / Math Formula Support**: Full math formatting via KaTeX (e.g. `$$E=mc^2$$` or `$$\vec{F}=m\vec{a}$$`).
   - Bulk card importer (tab-separated or comma-separated lines).
   - Filter cards by deck, search query, or learning state (*New*, *Learning*, *Review*).

5. **SM-2 Spaced Repetition Algorithm**:
   - Tracks **Ease Factor** (default 2.50), **Interval** (days), **Repetitions**, and **Lapses**.
   - 4-grade rating system:
     - **1: Again** (Reset interval to 10 minutes, decreases ease factor)
     - **2: Hard** (1.2x interval modifier, slight ease decrease)
     - **3: Good** (Multiplies interval by Ease Factor)
     - **4: Easy** (Multiplies interval by Ease Factor + bonus, increases ease)
   - Dynamic interval previews displayed on each rating button (e.g. `<10m`, `1d`, `3d`, `7d`).

6. **Interactive Study Session**:
   - 3D card flip animation.
   - **Keyboard shortcuts**:
     - `Space` or `Enter`: Flip card / Show answer
     - `1`, `2`, `3`, `4`: Submit rating
     - `H`: Toggle hint
   - Real-time progress bar and session completion summary.

7. **Analytics & Retention Dashboard**:
   - **90-Day Study Activity Heatmap** (Monochrome contribution grid).
   - **Retention Rate**: % of reviews rated Good/Easy.
   - **Rating Breakdown**: Visual distribution of your recall ratings.
   - **14-Day Due Forecast**: Predictions of upcoming review workload.

---

## 🚀 Quickstart & Running the App

### 1. Environment & Dependencies
```powershell
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

### 2. Configure Database (.env)
```ini
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=anki_flashcards
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 3. Apply Migrations & Seed Demo Data
```powershell
python manage.py migrate
python manage.py seed_demo_data
```
> **Demo Account**:
> - **Username**: `demo_user`
> - **Password**: `demo1234`

### 4. Run Development Server
```powershell
python manage.py runserver
```
Visit [http://localhost:8000/](http://localhost:8000/) in your browser.

---

## 🧪 Running Unit Tests
```powershell
python manage.py test apps.cards.tests apps.decks.tests apps.study.tests apps.accounts.tests
```
