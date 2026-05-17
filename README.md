# YOU GOOD MUD? — The Human Benchmark of Gaming!

A browser-based gaming benchmark platform where users create accounts, play mini-games, and compete on leaderboards. Inspired by humanbenchmark.com, the app features three games, per-game leaderboards, a social Following system to track friends' scores, and a password recovery flow.

---

## Table of Contents

- [Group Members](#group-members)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Test Overview](#test-overview)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)

---

## Group Members

| UWA ID   | Name             | GitHub |
|----------|------------------|--------|
| 23848254 | Chris Jose       | [Chris-Jose](https://github.com/Chris-Jose) |
| 23808253 | Kai Fletcher     | [k-train-money](https://github.com/k-train-money) |
| 24471981 | Michael Anthony  | [SmackyDahFrog](https://github.com/SmackyDahFrog) |
| 23639945 | John Requina     | [johnreq](https://github.com/johnreq) |

**Repository:** <https://github.com/SmackyDahFrog/CITS3403-Project>

---

## Features

### Authentication & Account Management
- **Sign up / Log in / Log out** with secure password hashing (Werkzeug)
- **Username availability check** via live AJAX endpoint (rate-limited: 20 requests per 10 s per IP)
- **Profile customisation** — choose from 8 avatars and set a display name immediately after signup
- **Settings page** — update display name, avatar, or password at any time
- **Password recovery** — secret-question/answer flow (answer is hashed before storage)
- Global **CSRF protection** via Flask-WTF on all forms

### Mini-Games & Leaderboards

| Game | Goal | Scoring |
|------|------|---------|
| **Where's Wilson** (`/game1`) | Find Wilson hidden on a crowded screen as fast as possible — single difficulty | Fastest time wins |
| **RNG Tic-Tac-Toe** (`/tictactoe`) | Beat an AI opponent that has a ~15% chance of making a random move each turn | Tracks wins / losses / draws; fastest win time for ranking |
| **Snack-Time** (`/play/kai`) | Keep a snake fed for as long as possible | Longest survival time wins; avg eat-time breaks ties |

Each game has a live **Top 3 global leaderboard** and displays the current player's personal best.

### Social — Following
- Search for other players by username or display name (AJAX, rate-limited)
- Follow / unfollow players; a **Following** page lists everyone you follow with their scores

---

## Tech Stack

**Backend**
- Python 3.10+, Flask 3.1
- Flask-Login (session-based authentication)
- Flask-WTF / WTForms (form handling and CSRF protection)
- SQLAlchemy 2.0 (ORM), Flask-Migrate / Alembic (database migrations)
- Werkzeug (password hashing)

**Frontend**
- HTML5 / CSS3, JavaScript (vanilla)
- Jinja2 (template engine)

**Database**
- SQLite

**Testing**
- Python `unittest`, Selenium 4 (headless Chrome)

---

## Setup & Installation

Clone the repository, then run the one-shot setup script for your platform.

### Windows (PowerShell)

```powershell
git clone https://github.com/SmackyDahFrog/CITS3403-Project.git
cd CITS3403-Project
.\setup.ps1
```

If PowerShell blocks the script:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### macOS / Linux / WSL

```bash
git clone https://github.com/SmackyDahFrog/CITS3403-Project.git
cd CITS3403-Project
bash setup.sh
```

The script:
1. Creates a virtual environment in `venv/`
2. Installs all dependencies from `requirements.txt`
3. Applies the database migrations (`flask db upgrade`)

---

## Running the Application

Activate the virtual environment, then start Flask:

**Windows:**
```powershell
.\venv\Scripts\Activate.ps1
python run.py
```

**macOS / Linux / WSL:**
```bash
source venv/bin/activate
python run.py
```

Open <http://127.0.0.1:5000> — the login page should load.

### Quick smoke test

1. Click *Create one* → `/signup`. Register with username ≥ 4 chars and password ≥ 8 chars containing a digit.
2. You are redirected to `/customisation`. Pick an avatar and display name, click *Save & Start Playing* → `/stages`.
3. Play any game, then check the leaderboard.
4. Click the profile circle → *Logout* → back at `/`.
5. Try accessing `/stages` while logged out — you are bounced to login with `?next=/stages`.

### Resetting the database

```powershell
# PowerShell
Remove-Item app\user.db; python run.py
```
```bash
# bash
rm app/user.db && python run.py
```

---

## Running Tests

Activate the virtual environment first, then use one of the commands below.

### Run all tests

```bash
python -m unittest discover -s tests -v
```

### Run a specific test file

```bash
python -m unittest tests.test_auth -v
python -m unittest tests.test_kai -v
python -m unittest tests.test_game1 -v
python -m unittest tests.tictactoeTesting -v
```

### Run only Selenium tests

```bash
python -m unittest tests.test_selenium_auth -v
python -m unittest tests.test_kai_selenium -v
python -m unittest tests.test_game1_selenium -v
```

> **Selenium requirement:** Google Chrome must be installed. Selenium 4 manages ChromeDriver automatically.

---

## Test Overview

| File | Type | Feature | What it covers |
|------|------|---------|----------------|
| [tests/test_auth.py](tests/test_auth.py) | Unit | Authentication | Signup creates user and redirects; username availability check (available / taken / too short / invalid chars); rate limiting returns 429 after 20 requests; failed signup preserves username in form; passwords never echoed back in HTML |
| [tests/test_selenium_auth.py](tests/test_selenium_auth.py) | Selenium | Authentication | Login page renders correct fields; valid credentials redirect to `/stages`; wrong password shows alert; unknown username shows alert; logout returns to login; signup page renders all fields; valid signup redirects to `/customisation`; "Forgot password" link navigates correctly |
| [tests/test_kai.py](tests/test_kai.py) | Unit | Snack-Time | Login required to access `/play/kai`; canvas page renders when authenticated; valid run payload saved to DB; negative `time_ms` rejected with 400 and nothing stored; better run overwrites existing record; worse run keeps existing best and returns `is_new_best: false` |
| [tests/test_kai_selenium.py](tests/test_kai_selenium.py) | Selenium | Snack-Time | Unauthenticated user redirected to login; canvas and heading render when logged in; restart button is clickable; sound dropdown selection persists to `localStorage` across page reload; back-to-stages link works; leaderboard displays seeded top player |
| [tests/test_game1.py](tests/test_game1.py) | Unit | Where's Wilson | Login required to access `/game1`; page renders correct content; valid run saved with `is_new_best: true`; slower follow-up run keeps existing best and returns `is_new_best: false` |
| [tests/test_game1_selenium.py](tests/test_game1_selenium.py) | Selenium | Where's Wilson | Unauthenticated user redirected to login; page renders title and Wilson element; starting game and clicking Wilson shows result overlay with correct message |
| [tests/tictactoeTesting.py](tests/tictactoeTesting.py) | Unit + Selenium | RNG Tic-Tac-Toe | **Unit:** page loads when authenticated; API records win/loss/draw independently; best win time updated when faster and kept when slower; win without `time_ms` rejected (400); invalid result string rejected (400). **Selenium:** 9 cells present; timer ticking; end screen hidden on load; clicking a cell places X; winning triggers end screen with correct title and time format; win recorded in DB; `best_win_ms` matches displayed time |

---

## Database Schema

| Model | Key Fields | Purpose |
|-------|-----------|---------|
| `User` | `id`, `username` (unique), `password_hash`, `display_name`, `avatar`, `secret_question`, `secret_answer_hash` | Player accounts and profile data |
| `WheresWilsonRun` | `user_id` (unique FK), `time_ms` | Personal best for Where's Wilson (one row per player) |
| `TicTacToeRun` | `user_id` (unique FK), `wins`, `losses`, `draws`, `best_win_ms` | Cumulative Tic-Tac-Toe stats per player |
| `KaiRun` | `user_id` (FK), `time_ms`, `avg_eat_ms`, `eat_count` | Best Snack-Time run per player |
| `Follow` | `follower_id`, `followed_id` (FKs), unique pair constraint | Social follow relationships |
| `Score` | `user_id` (FK), `game`, `value` | Generic score store (used for leaderboard aggregation) |

Schema changes are tracked via Flask-Migrate. After pulling new migrations:
```bash
flask db upgrade
```

---

## Project Structure

```
CITS3403-Project/
├── run.py                    # App entry point
├── requirements.txt          # Python dependencies
├── setup.ps1 / setup.sh      # One-shot environment setup scripts
├── app/
│   ├── __init__.py           # Flask app factory, extensions init
│   ├── config.py             # DevelopmentConfig / TestingConfig
│   ├── models.py             # SQLAlchemy models
│   ├── forms.py              # WTForms definitions
│   ├── routes.py             # All routes and API endpoints
│   ├── static/
│   │   ├── css/              # Per-page stylesheets
│   │   ├── js/               # Per-page JavaScript
│   │   ├── images/           # Avatars, game assets, logo
│   │   └── sounds/           # Game audio files
│   └── templates/
│       ├── base.html         # Master layout with navbar
│       ├── MainPage.html     # Login page
│       ├── signup.html       # Registration form
│       ├── customisation.html
│       ├── settings.html
│       ├── stages.html       # Game selection hub
│       ├── game1.html        # Where's Wilson
│       ├── ticTacToe.html    # RNG Tic-Tac-Toe
│       ├── games/kai.html    # Snack-Time
│       ├── following.html    # Followed players list
│       └── forgot_password*.html / reset_password.html
├── migrations/               # Flask-Migrate version history
└── tests/
    ├── test_auth.py
    ├── test_selenium_auth.py
    ├── test_kai.py
    ├── test_kai_selenium.py
    ├── test_game1.py
    ├── test_game1_selenium.py
    └── tictactoeTesting.py
```
