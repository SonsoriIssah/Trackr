from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from reminders import check_reminders
from apscheduler.schedulers.background import BackgroundScheduler
from task_breakdown import breakdown_goal
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schema.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = ''          # suppress default flash


# ── Models ────────────────────────────────────────────────────────────────────

class User(db.Model, UserMixin):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    todos         = db.relationship('Todo', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Todo(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    task_name         = db.Column(db.String,  nullable=False)
    category          = db.Column(db.String,  nullable=False)
    priority          = db.Column(db.String,  nullable=False)
    status            = db.Column(db.String,  nullable=False, default='Uncompleted')
    deadline          = db.Column(db.DateTime, nullable=False)
    reminder_time     = db.Column(db.DateTime, nullable=False)
    email             = db.Column(db.String,  nullable=False)
    message_delivered = db.Column(db.Boolean, default=False)
    user_id           = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ── DB init — auto-migrate: if the User table is missing, rebuild cleanly ─────

with app.app_context():
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(db.engine)
    if 'user' not in inspector.get_table_names():
        db.drop_all()
    db.create_all()


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        if len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif User.query.filter_by(username=username).first():
            error = 'That username is already taken.'
        elif User.query.filter_by(email=email).first():
            error = 'An account with that email already exists.'
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home'))

    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        error = 'Invalid username or password.'

    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ── Task routes ────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def home():
    todos = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('home.html', todos=todos)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        deadline      = datetime.strptime(request.form['deadline'],      '%Y-%m-%dT%H:%M')
        reminder_time = datetime.strptime(request.form['reminder_time'], '%Y-%m-%dT%H:%M')
        new = Todo(
            task_name     = request.form['task_name'],
            category      = request.form['category'],
            priority      = request.form['priority'],
            deadline      = deadline,
            reminder_time = reminder_time,
            email         = request.form['email'],
            user_id       = current_user.id
        )
        db.session.add(new)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create.html')


@app.route('/edit/<int:id>')
@login_required
def edit(id):
    todo = db.session.get(Todo, id)
    if not todo or todo.user_id != current_user.id:
        return redirect(url_for('home'))
    return render_template('edit.html', todo=todo)


@app.route('/save/<int:id>', methods=['GET', 'POST'])
@login_required
def save(id):
    todo = db.session.get(Todo, id)
    if not todo or todo.user_id != current_user.id:
        return redirect(url_for('home'))
    if request.method == 'POST':
        todo.task_name     = request.form['task_name']
        todo.category      = request.form['category']
        todo.priority      = request.form['priority']
        todo.status        = request.form['status']
        todo.deadline      = datetime.strptime(request.form['deadline'],      '%Y-%m-%dT%H:%M')
        todo.reminder_time = datetime.strptime(request.form['reminder_time'], '%Y-%m-%dT%H:%M')
        todo.email         = request.form['email']
        db.session.commit()
        return redirect(url_for('home'))
    return redirect(url_for('edit', id=id))


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    todo = db.session.get(Todo, id)
    if todo and todo.user_id == current_user.id:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for('home'))


# ── AI routes ─────────────────────────────────────────────────────────────────

@app.route('/breakdown', methods=['POST'])
@login_required
def breakdown():
    data = request.get_json(silent=True) or {}
    goal = data.get('goal', '').strip()
    if not goal:
        return jsonify({'error': 'No goal provided'}), 400
    return jsonify({'subtasks': breakdown_goal(goal)})


@app.route('/create-all', methods=['POST'])
@login_required
def create_all():
    data          = request.get_json(silent=True) or {}
    subtasks      = data.get('subtasks', [])
    category      = data.get('category', '').strip()
    priority      = data.get('priority', '').strip()
    deadline_str  = data.get('deadline', '').strip()
    reminder_str  = data.get('reminder_time', '').strip()
    email         = data.get('email', '').strip()

    if not all([subtasks, category, priority, deadline_str, reminder_str, email]):
        return jsonify({'error': 'All fields are required'}), 400

    try:
        deadline      = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        reminder_time = datetime.strptime(reminder_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    for task_name in subtasks:
        db.session.add(Todo(
            task_name=task_name, category=category, priority=priority,
            deadline=deadline, reminder_time=reminder_time,
            email=email, user_id=current_user.id
        ))
    db.session.commit()
    return jsonify({'created': len(subtasks)})


# ── Scheduler ─────────────────────────────────────────────────────────────────

scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', minutes=1, args=[db, Todo, app])
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
