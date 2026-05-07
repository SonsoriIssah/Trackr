from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schema.db'

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    task_name = db.Column(db.String, nullable = False)
    category = db.Column(db.String, nullable = False)
    priority = db.Column(db.String, nullable = False)
    status = db.Column(db.String, nullable=False, default='Uncompleted')
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
        new = Todo(task_name=task_name,category=category,priority=priority)
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
   
@app.route('/delete/<id>',methods=['POST'])
def delete(id):
    todo = Todo.query.get(id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)