# YOU GOOD MUD? — The Human Benchmark of Gaming!

A browser-based gaming benchmark platform where users create accounts, play mini-games, and compete on leaderboards. Inspired by humanbenchmark.com, the app features three games, per-game leaderboards, a social Following system to track friends' scores, and a password recovery flow.

---

## Group Members

| UWA ID   | Name             | GitHub Username |
|----------|------------------|-----------------|
| 23848254 | Chris Jose       | Chris-Jose      |
| 23808253 | Kai Fletcher     | k-train-money   |
| 24471981 | Michael Anthony  | SmackyDahFrog   |
| 23639945 | John Requina     | johnreq         |

---

## The Three Games

| Game | Description |
|------|-------------|
| **Where's Wilson** | Find Wilson hidden in a scene as fast as possible — three difficulty tiers |
| **RNG Tic-Tac-Toe** | Beat a minimax AI that makes a random move ~5% of the time |
| **Snack-Time** | Survive as long as possible eating snacks — scored by survival time and eat rate |

---

## Technologies Used

**Backend**
- Python 3.10+
- Flask (web framework)
- Flask-Login (session-based authentication)
- Flask-WTF / WTForms (form handling and CSRF protection)
- SQLAlchemy (ORM)
- Flask-Migrate / Alembic (database migrations)
- Werkzeug (password hashing)

**Frontend**
- HTML5 / CSS3
- Bootstrap 5 (UI framework)
- JavaScript (vanilla, no frameworks)
- Jinja2 (template engine)

**Database**
- SQLite

**Testing**
- Python unittest
- Selenium WebDriver (headless Chrome)

---

## Project Structure

```
CITS3403-Project/
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── models.py            # User, Score, KaiRun, WheresWilsonRun, TicTacToeRun, Follow
│   ├── routes.py            # All route handlers and API endpoints
│   ├── forms.py             # WTForms: login, signup, customisation, settings, forgot password
│   ├── config.py            # DevelopmentConfig, TestingConfig
│   ├── static/
│   │   ├── css/             # Per-page stylesheets
│   │   ├── js/              # Per-page JavaScript
│   │   └── images/          # Avatars, game assets, logo
│   └── templates/
│       ├── base.html        # Base layout with sidebar nav
│       ├── MainPage.html    # Login page
│       ├── signup.html      # Registration page
│       ├── customisation.html  # Post-signup profile setup
│       ├── stages.html      # Game selection screen
│       ├── game1.html       # Where's Wilson
│       ├── ticTacToe.html   # RNG Tic-Tac-Toe
│       ├── games/kai.html   # Snack-Time
│       ├── following.html   # Follow / unfollow users
│       ├── settings.html    # Account settings
│       └── forgot_password*.html  # Password recovery flow
├── migrations/              # Alembic migration files
├── tests/
│   ├── test_auth.py         # Unit tests: signup, login, username checks
│   ├── test_kai.py          # Unit tests: Snack-Time game logic
│   ├── test_selenium_auth.py     # Selenium: login, signup, logout, forgot password
│   └── test_kai_selenium.py      # Selenium: Snack-Time game flows
├── config.py                # App configuration
├── run.py                   # Entry point
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.10 or higher
- pip (comes with Python)
- Git
- Google Chrome + ChromeDriver (for Selenium tests only)

---

## Launching the Application

1. **Clone the repository**
   ```bash
   git clone https://github.com/SmackyDahFrog/CITS3403-Project.git
   cd CITS3403-Project
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```
   SECRET_KEY=your-secret-key-here
   ```
   Generate a secure key with:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

5. **Apply database migrations**
   ```bash
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```
   Open your browser at `http://127.0.0.1:5000`.

---

## Running the Tests

### Unit Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Or run individual files:

```bash
python -m unittest tests.test_auth -v
python -m unittest tests.test_kai -v
```

### Selenium Tests

Requires Chrome and ChromeDriver installed.

```bash
pip install selenium
python -m unittest tests.test_selenium_auth -v
python -m unittest tests.test_kai_selenium -v
```

> Each Selenium test starts a live Flask server automatically — no manual server setup required.

### Test File Overview

| File | Type | What it covers |
|------|------|----------------|
| `test_auth.py` | Unit | Signup, login, username availability checks, rate limiting |
| `test_kai.py` | Unit | Snack-Time score submission, leaderboard queries |
| `test_selenium_auth.py` | Selenium | Login, logout, signup, wrong credentials, forgot password link |
| `test_kai_selenium.py` | Selenium | Snack-Time game load and play flows |
