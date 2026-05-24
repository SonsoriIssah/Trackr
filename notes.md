# Trackr — Project Notes

## Stack
- **Flask** — web framework
- **SQLAlchemy** — ORM (maps Python classes to database tables)
- **SQLite** — local database (`instance/schema.db`)
- **APScheduler** — runs background jobs on a timer
- **smtplib** — Python's built-in email library
- **python-dotenv** — loads `.env` file into environment variables

---

## Project Structure
```
Trackr/
├── app.py            # Main Flask app, routes, scheduler setup
├── reminders.py      # Email logic and scheduled job
├── .env              # Secret credentials (never push to GitHub)
├── .gitignore        # Should include .env and instance/
├── instance/
│   └── schema.db     # SQLite database (auto-created)
└── templates/
    ├── home.html
    ├── create.html
    └── edit.html
```

---

## Database Model
```python
class Todo(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    task_name        = db.Column(db.String, nullable=False)
    category         = db.Column(db.String, nullable=False)
    priority         = db.Column(db.String, nullable=False)
    status           = db.Column(db.String, nullable=False, default='Uncompleted')
    deadline         = db.Column(db.DateTime, nullable=False)
    reminder_time    = db.Column(db.DateTime, nullable=False)
    email            = db.Column(db.String, nullable=False)
    message_delivered = db.Column(db.Boolean, default=False)
```

**Key rules:**
- `deadline` and `reminder_time` are stored as `DateTime` objects, not strings
- Form inputs come in as strings — convert with `datetime.strptime(value, '%Y-%m-%dT%H:%M')`
- `message_delivered` starts as `False` and is set to `True` after the reminder email is sent — prevents duplicate emails

---

## Routes
| Method | Route | What it does |
|--------|-------|--------------|
| GET | `/` | Shows all tasks |
| GET | `/create` | Shows the create form |
| POST | `/create` | Saves new task to database |
| GET | `/edit/<id>` | Shows edit form pre-filled with task data |
| POST | `/save/<id>` | Updates task in database |
| POST | `/delete/<id>` | Deletes task from database |

---

## Reminder System

### How it works
1. APScheduler runs `check_reminders()` every 60 seconds in a background thread
2. The function queries for tasks where `reminder_time <= now` AND `message_delivered == False`
3. For each due task, it sends an email and sets `message_delivered = True`
4. `db.session.commit()` saves that change so the email is never sent twice

### Why `app.app_context()` is needed
APScheduler runs outside Flask's request cycle. Flask-SQLAlchemy needs the app context to know which database to use. Without it you get: `RuntimeError: Working outside of application context.`

### Why we pass `db`, `Todo`, `app` as parameters
`reminders.py` needs these from `app.py`. Importing them directly causes a **circular import** (app.py imports reminders.py, reminders.py imports app.py). Passing them as function arguments breaks the cycle.

---

## Email Setup (Gmail)
- Gmail requires an **App Password** — your normal password will not work
- App Passwords require **2-Step Verification** to be enabled on your Google account
- Generate one at: myaccount.google.com → Security → App passwords

### `.env` file format
```
EMAIL_ADDRESS=yourgmail@gmail.com
EMAIL_PASSWORD=your16characterapppassword
```

### Why `.env` and not hardcoded?
Hardcoding credentials in your source code exposes them when you push to GitHub. Environment variables keep secrets out of version control.

---

## Key Concepts Learned

### SQLAlchemy ORM
- `db.Column(type, constraints)` defines a column
- `db.session.add(obj)` stages a new record
- `db.session.commit()` saves all staged changes
- `Model.query.filter(conditions).all()` queries with conditions
- `Model.query.get(id)` fetches a single record by primary key

### SQLAlchemy filter operators
```python
Model.field == value      # equals
Model.field != value      # not equals
Model.field <= value      # less than or equal
Model.field >= value      # greater than or equal
```

### datetime conversion
```python
# String from HTML form → Python datetime object
deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')

# Python datetime → HTML datetime-local format (for pre-filling edit form)
todo.deadline.strftime('%Y-%m-%dT%H:%M')
```

### APScheduler setup
```python
scheduler = BackgroundScheduler()
scheduler.add_job(function, 'interval', minutes=1, args=[arg1, arg2])
scheduler.start()  # call before app.run()
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `no such column: todo.deadline` | Database was created before new columns were added | Delete `instance/schema.db` and restart |
| `RuntimeError: Working outside of application context` | APScheduler runs outside Flask | Wrap database code in `with app.app_context():` |
| `ModuleNotFoundError: No module named 'dotenv'` | Package not installed | `pip install python-dotenv` |
| `ModuleNotFoundError: No module named 'apscheduler'` | Package not installed | `pip install apscheduler` |
| `NoneType has no attribute 'encode'` | `.env` not loaded or variables missing | Check `.env` exists, `load_dotenv()` is called before `os.environ.get()` |
| `SMTPAuthenticationError` | Wrong Gmail password | Use App Password, not your regular Gmail password |

---

## What's Left
- [ ] Update `save` route to handle `deadline`, `reminder_time`, `email` fields on edit
- [ ] Deploy to Render with PostgreSQL (same process as URL Shortener)
- [ ] Write unit tests with pytest
- [ ] Professional README
- [ ] Push to GitHub
