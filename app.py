import os
import secrets
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone 
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, jsonify, session, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Todo, Like, Image
from flask_mail import Mail, Message
from config import Config
import json

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Enable SQL logging
# config from config.py
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# initialize flask mail 
mail = Mail(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "warning"
 
# debug 
# import inspect
# print("Path to User model:", inspect.getfile(User))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

import string, random

def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def load_tasks():
    if os.path.exists('tasks.json'):
        with open('tasks.json', 'r') as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open('tasks.json', 'w') as f:
        json.dump(tasks, f)

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Max size is 2MB.', 'error')
    return redirect(request.referrer or url_for('uploadtoforum')), 413


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@login_manager.unauthorized_handler
def unauthorized():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': False,
            'error': 'Authentication required'
        }), 401  # Unauthorized
    else:
        flash('You need to be logged in to perform this action.', 'warning')
        return redirect(url_for('login', next=request.url))

@app.route('/fullcard/<int:id>', methods=['GET'])
def fullcard(id):
    task = Todo.query.get_or_404(id)
    if not task.approved and not (current_user.is_authenticated and current_user.is_admin):
        flash('This challenge is not approved yet')
        return redirect(url_for('forum'))
    
    return render_template('fullcard.html', task=task)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', "succes")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username', "").strip()
        password = request.form.get('password', "").strip()
        print(f"Login attempt - Username/Email: {username_or_email}")  # Debug log
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if user:
            print(f"User found in database")  # Debug log
            if user.check_password(password):
                print(f"Password correct, logging in")  # Debug log
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                print(f"Password incorrect")  # Debug log
                flash('Invalid password', "error")
        else:
            print(f"User not found")  # Debug log
            flash('No account found with that username or email', "error")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in.', "succes")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            flash('Passwords do not match', "error")
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', "error")
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', "error")
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', "succes")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    if current_user.is_master or current_user.is_admin:
        challenges = Todo.query.all()
        users = User.query.all()
        return render_template('admin.html', challenges=challenges, users=users)
    
    if not current_user.is_authenticated:
        flash('Please log in first.')
        return redirect(url_for('login'))
    
    if not current_user.is_master or not current_user.is_admin:
        flash('You are not authorized to view this page.')
        return redirect(url_for('index'))
    flash('error')
    return redirect(url_for('index'))
    
@app.route('/admin/approve_challenge/<int:id>')
@login_required
def approve_challenge(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    challenge = Todo.query.get_or_404(id)
    challenge.approved = True
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_challenge/<int:id>')
@login_required
def delete_challenge(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    challenge = Todo.query.get_or_404(id)
    db.session.delete(challenge)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<int:id>')
@login_required
def delete_user(id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    if user.is_admin:
        flash('Cannot delete admin users')
        return redirect(url_for('admin'))
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))

# app.py

# ... (existing imports and configurations) ...

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = user.set_reset_token() # Generate and save the token
            
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message(
                subject='Password Reset Request',
                sender=app.config['MAIL_USERNAME'], # Use app.config for sender
                recipients=[user.email]
            )
            msg.body = f"""To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
"""
            try:
                mail.send(msg)
                flash('A password reset link has been sent to your email.', 'info')
            except Exception as e:
                flash(f'Failed to send email. Please try again later. Error: {str(e)}', 'error')
                db.session.rollback() # Rollback the token generation if email fails
                print(f"Email sending error: {e}") # Log the error for debugging
        else:
            # It's good practice not to reveal if an email exists for security reasons
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        flash('That is an invalid or expired token.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            flash('Please enter both password and confirm password.', 'error')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)

        user.set_password(password)
        user.reset_token = None # Clear the token after successful reset
        user.reset_token_expiration = None # Clear the expiration
        db.session.commit()
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('reset.html', token=token)

# Remove or modify the reset_user_password route if it's only for master users
# If it's intended for master users to force reset, it should also use a token or similar
# The current implementation of reset_user_password directly giving a password is less secure
# for general use, but might be acceptable for an internal admin tool with highly trusted users.
# For public facing resets, the token-based approach is crucial.
@app.route('/reset_user_password/<int:id>', methods=['GET'])
@login_required
def reset_user_password(id):
    # Only master users can reset passwords
    if not current_user.is_master:
        abort(403)

    user = User.query.get_or_404(id)
    new_password = generate_random_password() # This generates a raw password
    user.set_password(new_password)
    db.session.commit()
    
    msg = Message(
        subject='Password reset', 
        sender=app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    msg.body = f"Hey, your password has been reset by an administrator.\n The new password is: {new_password}"    
    
    try:
        mail.send(msg)
        flash(f"Password for user '{user.username}' has been reset, and email sent.")
    except Exception as e:
        flash(f"Password for user '{user.username}' has been reset, but failed to send email. Error: {str(e)}", 'error')
        print(f"Admin forced reset email error: {e}") # Log the error
        
    return redirect(url_for('admin'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/forum')
def forum():
    vakfilter = request.args.get('vakfilter', '')
    sortfilter = request.args.get('sortfilter', 'newest')
    username = current_user.username if current_user.is_authenticated else None

    # Only show approved challenges unless user is admin
    query = Todo.query
    if not (current_user.is_authenticated and current_user.is_admin):
        query = query.filter_by(approved=True)
    
    if vakfilter:
        query = query.filter_by(category=vakfilter)
    
    if sortfilter == 'personal':
        if current_user.is_authenticated:
            query = query.join(User).filter(User.username == current_user.username)       
        else:
            flash('log in to filter by own challenge', "error")

    elif sortfilter == 'newest':
        query = query.order_by(Todo.date_created.desc())

    elif sortfilter == 'oldest':
        query = query.order_by(Todo.date_created.asc())

    elif sortfilter == 'likes':
        query = query.order_by(Todo.likes.desc())

    tasks = query.all()
    return render_template('forum.html', tasks=tasks, sortfilter=sortfilter)

@app.route('/uploadtoforum', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        main_question = request.form.get('mainQuestion', '').strip()
        sub_questions = request.form.get('subQuestions', '').strip()
        description = request.form.get('description', '').strip()
        end_product = request.form.get('endProduct', '').strip()
        category = request.form.get('categorie', '').strip()
        name = current_user.username
        
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

        new_task = Todo(
            title=title,
            name=name,
            main_question=main_question,
            sub_questions=sub_questions,
            description=description,
            end_product=end_product,
            category=category,
            image=image_filename,
            author_id=current_user.id,
            approved=current_user.is_admin,
            likes=0
        )

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/forum')
        except Exception as e:
            print(f"Error adding challenge: {str(e)}")  # Add this for debugging
            return 'There was an issue adding your challenge'
    
    return render_template('uploadtoforum.html')

@app.route('/like/<int:id>', methods=['GET', 'POST'])
@login_required
def like(id):
    try:
        todo = Todo.query.get_or_404(id)
        existing_like = Like.query.filter_by(
            todo_id=id,
            user_id=current_user.id
        ).first()
        
        liked = False
        if existing_like:
            db.session.delete(existing_like)
            todo.likes = max(0, todo.likes - 1)  # Ensure likes don't go below 0
        else:
            like = Like(todo_id=id, user_id=current_user.id)
            db.session.add(like)
            todo.likes += 1
            liked = True
        
        db.session.commit()

        # Add task to liked_tasks session if liked, remove if unliked
        liked_tasks = session.get('liked_tasks', [])
        if liked and id not in liked_tasks:
            liked_tasks.append(id)
        elif not liked and id in liked_tasks:
            liked_tasks.remove(id)
        session['liked_tasks'] = liked_tasks
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'likes': todo.likes,
                'liked': liked,
                'success': True
            })
        
        # For regular form submissions, redirect back
        next_page = request.referrer or url_for('forum')
        return redirect(next_page)
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        flash('Error processing like')
        return redirect(url_for('forum'))

@app.route("/like_status/<int:todo_id>")
@login_required
def like_status(todo_id):
    liked = Like.query.filter_by(todo_id=todo_id, user_id=current_user.id).first() is not None
    like_count = Like.query.filter_by(todo_id=todo_id).count()
    
    return jsonify(success=True, liked=liked, likes=like_count)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    task = Todo.query.get_or_404(id)
    
    # Check authorization
    if not (current_user.id == task.author_id or current_user.is_admin):
        flash('You are not authorized to edit this challenge')
        return redirect(url_for('forum'))

    if request.method == 'GET':
        return render_template('update.html', task=task)

    if request.method == 'POST':
        print(f"Updating task {id} by user {current_user.username}")  # Debug log
        task.title = request.form.get('title')
        task.main_question = request.form.get('mainQuestion').strip()
        task.sub_questions = request.form.get('subQuestions').strip()
        task.description = request.form.get('description').strip()
        task.end_product = request.form.get('endProduct').strip()
        task.category = request.form.get('categorie').strip()
        # name is not updated as it should stay as the original author's username
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                task.image = filename
        
        try:
            db.session.commit()
            flash('Challenge updated successfully')
            return redirect(url_for('forum'))
        except Exception as e:
            print(f"Error updating challenge: {str(e)}")  # Debug logging
            db.session.rollback()
            flash('There was an issue updating your challenge')
            return redirect(url_for('forum'))

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    # Get the task or return 404
    task_to_delete = Todo.query.get_or_404(id)
    
    # Check authorization
    if not (current_user.id == task_to_delete.author_id or current_user.is_admin):
        flash('You are not authorized to delete this challenge')
        return redirect(url_for('forum'))
    
    try:
        # Delete likes
        Like.query.filter_by(todo_id=id).delete()
        
        # Delete images
        Image.query.filter_by(todo_id=id).delete()
        
        # Delete the task
        db.session.delete(task_to_delete)
        
        # Commit the transaction
        db.session.commit()
        
        flash('Challenge deleted successfully')
        return redirect(url_for('forum'))
    except Exception as e:
        print(f"Error deleting challenge {id}: {str(e)}")  # Debug logging
        db.session.rollback()
        flash('There was a problem deleting that challenge')
        return redirect(url_for('forum'))

# change this folder to the actual folder off the upload folder 
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Max 2 MB upload
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)