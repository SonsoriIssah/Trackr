# Trackr

A CRUD-based task management app built with Flask and SQLAlchemy. Users can create, view, update, and delete tasks with categories, priority levels, and status tracking.

---

## Features

- Create tasks with a name, category, and priority
- View all tasks on the home page
- Edit existing tasks including status updates
- Delete tasks
- Default status set to "Uncompleted" on creation
- Data persisted in a local SQLite database

---

## Tech Stack

| Layer    | Tool              |
|----------|-------------------|
| Backend  | Python / Flask    |
| Database | SQLite            |
| ORM      | Flask-SQLAlchemy  |
| Frontend | HTML / Jinja2     |

---

## Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/SonsoriIssah/Trackr.git
cd Trackr
```

**2. Create and activate a virtual environment**
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the app**
```bash
flask --app app run
```

**5. Open in your browser**
```
http://127.0.0.1:5000
```

---

## Project Structure

```
trackr/
├── app.py               # Flask app, routes, and database models
├── requirements.txt     # Project dependencies
├── README.md            # Project documentation
└── templates/
    ├── home.html        # Home page — list of all tasks
    ├── create.html      # Create a new task
    └── edit.html        # Edit an existing task
```

---

## Routes

| Route          | Method | Description                        |
|----------------|--------|------------------------------------|
| `/`            | GET    | Display all tasks                  |
| `/create`      | GET    | Show create task form              |
| `/create`      | POST   | Save new task to database          |
| `/edit/<id>`   | GET    | Show edit form for a task          |
| `/save/<id>`   | POST   | Save updated task                  |
| `/delete/<id>` | POST   | Delete a task                      |

---

## Data Model

| Column      | Type    | Description                              |
|-------------|---------|------------------------------------------|
| `id`        | INTEGER | Primary key, auto-incremented            |
| `task_name` | TEXT    | Name of the task                         |
| `category`  | TEXT    | Category: School, Personal, Work, etc.   |
| `priority`  | TEXT    | Priority: High, Medium, or Low           |
| `status`    | TEXT    | Status: Uncompleted, In Progress, Done   |

---

## Authors

**Issah Sonsori Abdul-Wasiu** — Backend  
BSc Computer Science, KNUST — Class of 2028  
[GitHub](https://github.com/SonsoriIssah)
