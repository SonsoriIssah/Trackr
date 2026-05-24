from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from reminders import check_reminders
from apscheduler.schedulers.background import BackgroundScheduler
from task_breakdown import breakdown_goal

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schema.db'

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    task_name = db.Column(db.String, nullable = False)
    category = db.Column(db.String, nullable = False)
    priority = db.Column(db.String, nullable = False)
    status = db.Column(db.String, nullable=False, default='Uncompleted')
    deadline =  db.Column(db.DateTime, nullable = False)
    reminder_time = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String,nullable=False)
    message_delivered = db.Column(db.Boolean,default=False)
with app.app_context():
    db.create_all()
@app.route('/')
def home():
    todos = Todo.query.all()
    return render_template('home.html', todos = todos)

@app.route('/create', methods = ['GET','POST'])
def create():
    if request.method == 'POST':
        task_name = request.form['task_name']
        category = request.form['category']
        priority = request.form['priority']
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')
        reminder_time = datetime.strptime(request.form['reminder_time'], '%Y-%m-%dT%H:%M')
        email = request.form['email']
        new = Todo(task_name=task_name,category=category,priority=priority,deadline=deadline,reminder_time=reminder_time,email=email)
        db.session.add(new)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template('create.html')


@app.route('/edit/<id>')
def edit(id):
   todo = Todo.query.get(id)
   return render_template('edit.html',todo=todo)

@app.route( '/save/<id>',methods = ['GET','POST'])
def save(id):
   if request.method == 'POST':
        todo = Todo.query.get(id)
        todo.task_name = request.form['task_name']
        todo.category = request.form['category']
        todo.status = request.form['status']
        db.session.commit()
        return redirect(url_for('home'))
   else:
       return redirect(url_for('edit'))
   
@app.route('/breakdown', methods=['POST'])
def breakdown():
    data = request.get_json(silent=True) or {}
    goal = data.get('goal', '').strip()
    if not goal:
        return jsonify({'error': 'No goal provided'}), 400
    return jsonify({'subtasks': breakdown_goal(goal)})

@app.route('/create-all', methods=['POST'])
def create_all():
    data = request.get_json(silent=True) or {}
    subtasks = data.get('subtasks', [])
    category = data.get('category', '').strip()
    priority = data.get('priority', '').strip()
    deadline_str = data.get('deadline', '').strip()
    reminder_str = data.get('reminder_time', '').strip()
    email = data.get('email', '').strip()

    if not all([subtasks, category, priority, deadline_str, reminder_str, email]):
        return jsonify({'error': 'All fields are required'}), 400

    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        reminder_time = datetime.strptime(reminder_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    for task_name in subtasks:
        db.session.add(Todo(
            task_name=task_name,
            category=category,
            priority=priority,
            deadline=deadline,
            reminder_time=reminder_time,
            email=email
        ))
    db.session.commit()
    return jsonify({'created': len(subtasks)})

@app.route('/delete/<id>',methods=['POST'])
def delete(id):
    todo = Todo.query.get(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('home'))
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', minutes=1, args=[db, Todo,app])
if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)