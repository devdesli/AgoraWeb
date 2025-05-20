import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone 
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, jsonify, session, url_for
from models import db
from models import db, Todo, Like, Image
from flask import session
import json
import os

def load_tasks():
    if os.path.exists('tasks.json'):
        with open('tasks.json', 'r') as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open('tasks.json', 'w') as f:
        json.dump(tasks, f)


app = Flask(__name__)
app.secret_key = "supersecret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/home')
def home_redirect():
    return redirect(url_for('index'))

@app.route('/challenge/<int:id>', methods=['GET'])
def challenge_view(id):
    task = Todo.query.get_or_404(id)
    try: 
        return render_template('fullcard.html', tasks=[task])
    except:
        return "Error rendering template", 500

@app.route('/togglelike/<int:id>', methods=['POST'])
def toggle_like(id):
    todo = Todo.query.get_or_404(id)
    liked_tasks = session.get('liked_tasks', [])

    try:
        if id in liked_tasks:
            # Unlike
            Like.query.filter_by(todo_id=id).delete()
            todo.likes = max(0, todo.likes - 1)
            liked_tasks.remove(id)
        else:
            # Like
            new_like = Like(todo_id=id)
            db.session.add(new_like)
            todo.likes += 1
            liked_tasks.append(id)

        session['liked_tasks'] = liked_tasks
        db.session.commit()

        return redirect(request.referrer or url_for('forum'))
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            task.name = request.form.get('name', '')
            task.title = request.form.get('title', '')
            task.main_question = request.form.get('mainQuestion', '')
            task.sub_questions = request.form.get('subQuestions', '')
            task.description = request.form.get('description', '')
            task.end_product = request.form.get('endProduct', '')
            task.category = request.form.get('categorie', '')

            # Handle image upload
            image_file = request.files.get('image')
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(filepath)
                
                # Delete old image if it exists
                if task.image:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], task.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                task.image = filename

            # Save changes to database
            db.session.commit()
            return redirect(url_for('forum'))

        except Exception as e:
            db.session.rollback()
            return f"There was an issue updating the task: {str(e)}", 500

    # GET request - display the update form
    return render_template('update.html', task=task, categories=[
        "Aardrijkskunde", "Biologie", "Informatica", "Economie", 
        "Natuurkunde", "Maatschapijleer", "Lichamelijke opvoeding", 
        "Kunst en Cultuur", "Wiskunde", "Geschiedenis", "Engels",
        "Nederlands", "Frans", "Duits", "Handvaardigheid", 
        "Muziek", "Scheikunde", "Overig"
    ])

@app.route('/delete/<int:id>', methods=['POST'])
def delete_task(id):
    todo = Todo.query.get_or_404(id)
    try:
        # Also delete likes related to the task
        Like.query.filter_by(todo_id=todo.id).delete()
        db.session.delete(todo)
        db.session.commit()
        return redirect(url_for('forum'))
    except Exception as e:
        return f"There was an issue deleting the task: {str(e)}", 500

@app.route('/forum', methods=['POST', 'GET'])
def forum():
    query = Todo.query
    
    sortfilter = request.args.get('sortfilter', 'newest')  # Default to newest
    vakfilter = request.args.get('vakfilter')

    if vakfilter:
        query = query.filter_by(category=vakfilter)
    
    if sortfilter == 'newest':
        query = query.order_by(Todo.date_created.desc())
    elif sortfilter == 'oldest':
        query = query.order_by(Todo.date_created.asc())
    elif sortfilter == 'likes':
        query = query.order_by(Todo.likes.desc())
    
    todos = query.all()
    
    return render_template('forum.html', tasks=todos)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            new_image = Image(filename=filename)
            db.session.add(new_image)
            db.session.commit()

            return redirect('/uploadtoforum')
    return render_template('upload.html')

@app.route('/uploadtoforum', methods=['POST', 'GET'])
def uploadtoforum():
    if request.method == 'POST':
        task_name = request.form.get('name')
        task_title = request.form.get('title')
        task_main_question = request.form.get('mainQuestion')
        task_sub_questions = request.form.get('subQuestions')
        task_description = request.form.get('description')
        task_end_product = request.form.get('endProduct')
        task_category = request.form.get('categorie')
        task_image = request.files.get('image')

        if not task_name:
            return "Name field is required", 400

        image_filename = None
        if task_image and allowed_file(task_image.filename):
            image_filename = secure_filename(task_image.filename)
            task_image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        new_task = Todo(
            title=task_title,
            name=task_name,
            main_question=task_main_question,
            sub_questions=task_sub_questions,
            description=task_description,
            end_product=task_end_product,
            category=task_category,
            image=image_filename,
            likes=0
        )

        try:
            db.session.add(new_task)
            db.session.commit()

            todos = Todo.query.all()
            return redirect('/forum')
        except Exception as e:
            return f"There was an issue adding your task: {str(e)}"
    else:
        print("redirecting to upload to forum")
        return render_template('uploadtoforum.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)