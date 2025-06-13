from slugify import slugify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone 
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, jsonify, session, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Todo, Like, Image
from flask_mail import Mail, Message
from config import Config
import time
import os
import secrets
import json
import logging
from logging.handlers import RotatingFileHandler
import uuid


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Enable SQL logging
app.config.update(
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_SECURE=True
)

# config from config.py
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# --- Logging Setup ---
if not os.path.exists('logs'):
    os.mkdir('logs')

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] in %(module)s: %(message)s'
)

# General app log (INFO and above)
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=3)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Upload log (INFO and above)
upload_handler = RotatingFileHandler('logs/upload.log', maxBytes=10240, backupCount=3)
upload_handler.setLevel(logging.INFO)
upload_handler.setFormatter(formatter)
upload_logger = logging.getLogger('upload_logger')
upload_logger.setLevel(logging.INFO)
upload_logger.addHandler(upload_handler)

# Optional: if you want errors to also be logged separately
error_handler = RotatingFileHandler('logs/error.log', maxBytes=10240, backupCount=3)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)

# change this folder to the actual folder off the upload folder 
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Max 2 MB upload
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    return render_template('error.html', statusCode=404, message="The page you requested could not be found."), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', statusCode=500, message="An unexpected error occurred on our server. We are working to fix it!"), 500

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
    
@app.route('/card/<int:id>', defaults={'slug': None})
@app.route('/fullcard/<int:id>-<slug>', methods=['GET'])
def fullcard(id, slug):
    task = Todo.query.get_or_404(id)
    if not task.approved and not (current_user.is_authenticated and current_user.is_master or current_user.is_admin):
        flash('This challenge is not approved yet')
        return redirect(url_for('forum'))
    
    return render_template('fullcard.html', task=task)

@app.route('/mychallenges')
@login_required
def my_challenges():
    challenges = Todo.query.filter_by(author_id=current_user.id).order_by(Todo.date_created.desc()).all()
    return render_template('my_challenges.html', challenges=challenges)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', "succes")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username', "").strip()
        password = request.form.get('password', "").strip()
        app.logger.info(f"Login attempt - Username/Email: {username_or_email}")  # Debug log
        
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
        app_status = app.config['APP_STATUS']
        users = User.query.all()
        return render_template('admin.html', challenges=challenges, users=users, app_status=app_status)
    
    if not current_user.is_authenticated:
        flash('Please log in first.')
        return redirect(url_for('login'))
    
    if not current_user.is_master or not current_user.is_admin:
        flash('You are not authorized to view this page.')
        return redirect(url_for('index'))
    flash('error')
    return redirect(url_for('index'))

@app.route('/admin/send-email/', methods=["POST", "GET"])
@login_required
def admin_email():
    # Authorization check FIRST
    if not current_user.is_master and not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        subject = request.form.get('subject')
        input_text = request.form.get('input_text')

        if not subject or not input_text:
            flash("Subject and message body are required.", "error")
            return render_template('admin_email.html')

        # Get all user emails
        recipients = [user.email for user in User.query.all() if user.email]

        if not recipients:
            flash("No valid user emails found.", "error")
            return render_template('admin_email.html')

        msg = Message(
            subject=subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=["agorawebapplication@gmail.com"],
            bcc=recipients
        )
        msg.body = input_text

        try:
            mail.send(msg)
            flash("Email sucesfully sent to all users.")
        except Exception as e:
            flash(f"Sending email failed. Error: {str(e)}", 'error')
            print(f"Admin send email error: {e}")  # Log the error

    return render_template('admin_email.html')

    
@app.route('/admin/approve_challenge/<int:id>')
@login_required
def approve_challenge(id):
    if not (current_user.is_master or current_user.is_admin):
        return redirect(url_for('index'))
    challenge = Todo.query.get_or_404(id)
    challenge.approved = True
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_challenge/<int:id>')
@login_required
def delete_challenge(id):
    if not current_user.is_master and not current_user.is_admin:
        return redirect(url_for('index'))
    challenge = Todo.query.get_or_404(id)
    db.session.delete(challenge)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<int:id>')
@login_required
def delete_user(id):
    if not current_user.is_master or current_user.is_admin:
        return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    if user.is_admin and not current_user.is_admin:
        flash('Cannot delete admin users')
        return redirect(url_for('admin'))
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))

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
        flash("already logged in")
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

@app.route('/reset_user_password/<int:id>', methods=['POST']) # Change to POST for better security
@login_required
def reset_user_password(id):
    # Only master users can reset passwords
    if not current_user.is_master:
        abort(403)

    user = User.query.get_or_404(id)

    # Prevent master admin from resetting their own password this way (or other admins)
    if user.is_master and user.id == current_user.id:
        flash("You cannot reset your own master password this way.", "error")
        return redirect(url_for('admin'))

    # Generate a reset token for the user
    token = user.set_reset_token() # This method is already defined in your User model

    # Construct the reset URL
    reset_url = url_for('reset_password', token=token, _external=True)

    msg = Message(
        subject='Administrator initiated Password Reset Request',
        sender=app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    msg.body = f"""Hello {user.username},

An administrator has initiated a password reset for your account on Agora.

To set a new password, please visit the following link:
{reset_url}

This link is valid for a limited time. If you did not request this, or if you believe this is in error, please ignore this email. Your current password will remain unchanged until you follow the link and set a new one.

Thank you,
Agora Team
"""

    try:
        mail.send(msg)
        db.session.commit() # Commit the token to the database after successful email sending
        flash(f"Password reset link sent to '{user.username}' ({user.email}). User must use the link to set a new password.", "info")
    except Exception as e:
        db.session.rollback() # Rollback the token generation if email fails
        flash(f"Failed to send password reset email to '{user.username}'. Error: {str(e)}", 'error')
        print(f"Admin forced reset email error: {e}") # Log the error for debugging

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
    
    if vakfilter == 'personal':
        if current_user.is_authenticated:
            # Corrected line: Use author_id and current_user.id
            query = query.filter_by(author_id=current_user.id)
        else:
            flash('Log in to filter by your own challenges.', "error")
    elif vakfilter:
        query = query.filter_by(category=vakfilter)

    if sortfilter == 'newest':
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
        sub_questions_list = request.form.getlist('subQuestion[]')
        description = request.form.get('description', '').strip()
        end_product = request.form.get('endProduct', '').strip()
        category = request.form.get('categorie', '').strip()
        name = current_user.username
        sub_questions_json = json.dumps([q.strip() for q in sub_questions_list if q.strip()])
        
        image_filename = None
        if 'image' in request.files:
          file = request.files['image']
          if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            title_slug = slugify(title)
            timestamp = int(time.time())
            # Optionally use current_user.id instead of username if usernames may change
            custom_filename = f"{current_user.username}_{title_slug}_{timestamp}.{ext}"
            filename = secure_filename(custom_filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        # Create unique slug
        base_slug = slugify(title) or f"untitled-{uuid.uuid4().hex[:6]}"
        slug = base_slug
        counter = 1
        while Todo.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        new_task = Todo(
            title=title,
            name=name,
            main_question=main_question,
            sub_questions=sub_questions_json,
            description=description,
            end_product=end_product,
            category=category,
            image=image_filename,
            author_id=current_user.id,
            approved=current_user.is_admin or current_user.is_master,
            likes=0,
            slug=slug
        )

        try:
            db.session.add(new_task)
            db.session.commit()
            if not (current_user.is_master or current_user.is_admin):
                flash("When your challenge gets approved, you'll see it here.", "info")
            return redirect('/forum')
        except IntegrityError:
            db.session.rollback()
            flash("A challenge with a similar slug already exists. Try a different title.", "danger")
            return render_template('uploadtoforum.html')
        except Exception as e:
            db.session.rollback()
            print(f"Error adding challenge: {str(e)}")
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
        return render_template('update.html', task=task, sub_questions=task.get_sub_questions_list())

    if request.method == 'POST':
        print(f"Updating task {id} by user {current_user.username}")  # Debug log
        task.title = request.form.get('title')
        task.main_question = request.form.get('mainQuestion').strip()
        sub_questions_list = request.form.getlist('subQuestion[]')
        # Convert the list to a JSON string
        task.sub_questions = json.dumps([q.strip() for q in sub_questions_list if q.strip()])
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
        
        if not (current_user.is_admin or current_user.is_master):
            Todo.challenge.approved = False

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

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        file = request.files['image']
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            timestamp = int(time.time())
            
            # Create new filename: e.g., 1718307203_myimage.jpg
            filename = f"{current_user.username}_{timestamp}_{original_filename}"
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