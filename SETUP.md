# CITS3403-Project — You Good Mud?

Flask + SQLAlchemy web app for the CITS3403 group project.

## Quick start

**Windows (PowerShell):**

```powershell
.\setup.ps1
.\venv\Scripts\Activate.ps1
python run.py
```

**macOS / Linux / WSL:**

```bash
bash setup.sh
source venv/bin/activate
python run.py
```

The setup script creates a virtual environment in `venv/`, installs everything in `requirements.txt`, and applies the database migration. After it finishes, activate the venv and start the server.

Open <http://127.0.0.1:5000> — the login page should load.

## Project layout

```
app/
  __init__.py        # Flask app factory
  config.py          # Dev / Test config classes
  models.py          # User SQLAlchemy model
  forms.py           # WTForms: Login, Signup, Customisation
  routes.py          # main blueprint: /, /signup, /customisation, /stages, /logout
  static/{css,js,images}/
  templates/         # Jinja2 templates
migrations/          # Flask-Migrate version history
tests/test_auth.py   # unittest cases against in-memory SQLite
run.py               # entrypoint
```

## Click-through test

After `python run.py`, walk through these in the browser to confirm everything works:

1. **`/`** → click *Create one* → land on `/signup`.
2. Sign up with a new username (≥4 chars), password (≥8 chars including a digit), and matching confirmation. You should be redirected to `/customisation`.
3. Pick an avatar, type a display name, click *Save & Start Playing* → redirected to `/stages`.
4. Click your profile circle → *Logout* → back at `/`.
5. Try `/stages` while logged out → bounced back to login with a `?next=/stages` parameter.
6. Try signing up again with the same username → "That username is already taken."
7. Try mismatched passwords → "Passwords do not match."

## Running the unit tests

```
python -m unittest tests.test_auth -v
```

Expected output:

```
test_login_with_wrong_password_fails ... expected failure
test_signup_creates_user ... ok
OK (expected failures=1)
```

## Inspecting the database

`flask shell` drops you into a Python REPL with the app context loaded:

```python
>>> from app.models import User
>>> User.query.all()
>>> u = User.query.filter_by(username='kai').first()
>>> u.display_name, u.avatar
```

`exit()` to leave.

## Resetting the database

To wipe `app/user.db` and start over:

**PowerShell:** `Remove-Item app\user.db; python run.py`
**bash:** `rm app/user.db && python run.py`

The app re-creates the schema automatically on startup.

## Adding a schema change

When `app/models.py` changes (new column, new table, etc.):

```
flask db migrate -m "describe the change"
flask db upgrade
```

Commit the new file under `migrations/versions/`. Teammates run `flask db upgrade` after pulling.

## Common issues

- **`ModuleNotFoundError: No module named 'flask'`** — venv isn't activated. Re-run the activate command.
- **`ModuleNotFoundError: No module named 'click.decorators'`** — partial install. Wipe and reinstall: `Remove-Item -Recurse -Force venv` (PowerShell) or `rm -rf venv` (bash), then re-run setup.
- **`BuildError: Could not build url for endpoint 'main.X'`** — a template references a route that doesn't exist. Live endpoints: `main.login`, `main.signup`, `main.customisation`, `main.stages`, `main.logout`.
- **PowerShell "running scripts is disabled"** — once-off: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.
