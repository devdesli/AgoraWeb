from slugify import slugify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone 
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, jsonify, session, url_for, flash, abort, send_from_directory, make_response
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
import string, random
import re
from xhtml2pdf import pisa
import io
from flask_wtf import CSRFProtect
from forms import LoginForm, RegisterForm, AdminEmailForm, UploadForm, UploadToForumForm, LikeForm, ResetForm, ForgotForm, DeleteForm, ResetUserBtnForm, CSRFOnlyForm
from werkzeug.datastructures import CombinedMultiDict

UPLOAD_FOLDER = 'static/uploads'
# upload folder
# Call this before your routes

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
csrf = CSRFProtect(app)
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_ENABLED'] = True

def ensure_upload_directory():
    upload_dir = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    if not os.path.exists(upload_dir):
        try:
            os.makedirs(upload_dir, exist_ok=True)
            print(f"Created upload directory: {upload_dir}")
        except Exception as e:
            print(f"Error creating upload directory: {e}")
            raise
    return upload_dir

# Call this before your routes
ensure_upload_directory()


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

activity_handler = RotatingFileHandler('logs/activity.log', maxBytes=10240, backupCount=3, delay=True)
activity_handler.setLevel(logging.INFO)
activity_handler.setFormatter(formatter)
activity_logger = logging.getLogger('activity_logger')
activity_logger.setLevel(logging.INFO)
activity_logger.addHandler(activity_handler)


# Optional: if you want errors to also be logged separately
error_handler = RotatingFileHandler('logs/error.log', maxBytes=10240, backupCount=3)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)

# change this folder to the actual folder off the upload folder 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Max 2 MB upload
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

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
    user = User.query.get(int(user_id))
    if user:
        activity_logger.info(f"Loaded user: {user.username} (ID: {user.id})")
    else:
        activity_logger.warning(f"Tried to load non-existent user with ID: {user_id}")
    return user

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
        
# redirect automaticly for http not configed now
#@app.before_request
#def force_https():
    #if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
        #return redirect(request.url.replace('http://', 'https://', 1), code=301)
    
@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Max size is 2MB.', 'error')
    error_logger(f"Error 413, {error}")
    return redirect(request.referrer or url_for('uploadtoforum')), 


@app.errorhandler(404)
def not_found_error(error):
    error_logger.info(f"Error 404, {error}")
    return render_template('error.html', statusCode=404, message="The page you requested could not be found."), 404

@app.errorhandler(500)
def internal_error(error):
    error_logger.critical(f"CRITICAL ERROR WEBSITE OFLINE, {error}")
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
        activity_logger.info(f"Unauthorized handler")
        flash('You need to be logged in to perform this action.', 'warning')
        return redirect(url_for('login', next=request.url))


@app.route('/googleb81b129169642c35.html')
def google_verification():
    return send_from_directory('.', 'googleb81b129169642c35.html')

@app.route('/card/<int:id>', defaults={'slug': None})
@app.route('/fullcard/<int:id>-<slug>', methods=['GET'])
def fullcard(id, slug):
    task = Todo.query.get_or_404(id)
    likeform = CSRFOnlyForm()
    form = CSRFOnlyForm
    if not task.approved and not (current_user.is_authenticated and current_user.is_master or current_user.is_admin):
        app.logger.info(f"{task}, Not approved yet")
        flash('This challenge is not approved yet')
        return redirect(url_for('forum'))
    return render_template('fullcard.html', task=task, form=form, likeform=likeform)

@app.route('/challenge/download/<int:challenge_id>')
@login_required
def download_challenge_pdf(challenge_id):
    challenge = Todo.query.get_or_404(challenge_id)

    # Authorization: Only download if approved or owned by the user
    if not challenge.approved and current_user.is_authenticated:
        flash('You are not authorized to download this challenge.', 'error')
        return redirect(url_for('forum'))

    # Render HTML template with challenge data
    html = render_template("challenge_pdf_template.html", challenge=challenge)

    # Create PDF from HTML
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), result)

    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename=challenge_{challenge.slug}_{challenge.id}.pdf"
        return response
    else:
        flash("PDF generation failed.", "error")
        return redirect(url_for('fullcard', id=challenge.id))
    
@app.route('/mychallenges')
@login_required
def my_challenges():
    form = DeleteForm()
    challenges = Todo.query.filter_by(author_id=current_user.id).order_by(Todo.date_created.desc()).all()
    return render_template('my_challenges.html', challenges=challenges, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = CSRFOnlyForm()

    if current_user.is_authenticated:
        app.logger.info(f"{current_user.username} already logged in")
        flash('You are already logged in.', "succes")
        return redirect(url_for('index'))

    if form.validate_on_submit():  # this only checks CSRF token
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        app.logger.info(f"Login attempt - Username/Email: {username_or_email}")  # Debug log
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if user:
            print(f"User found in database")  # Debug log
            if user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                app.logger.info(f"{username_or_email}, logged in succesfully")
                return redirect(next_page or url_for('index'))
            else:
                app.logger.error(f"Password incorrect for {username_or_email}")  # Debug log
                flash('Invalid password', "error")
        else:
            app.logger.error(f"User not found {username_or_email}")  # Debug log
            flash('No account found with that username or email', "error")
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = CSRFOnlyForm()

    if current_user.is_authenticated:
        app.logger.info(f"{current_user}, already logged in")
        flash('You are already logged in.', "succes")
        return redirect(url_for('index'))
    
    if request.method == 'POST' and form.validate():
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            app.logger.error(f"Passwords for {username}, do not match")
            flash('Passwords do not match', "error")
            return redirect(url_for('register', form=form))
        
        if User.query.filter_by(username=username).first():
            app.logger.error(f"username {username} already exists")
            flash('Username already exists', "error")
            return redirect(url_for('register', form=form))
        
        if User.query.filter_by(email=email).first():
            app.logger.error(f"email {email} already registered")
            flash('Email already registered', "error")
            return redirect(url_for('register', form=form))
        
        user = User(username=username, email=email)
        try: 
          user.set_password(password)
          db.session.add(user)
          db.session.commit()
          app.logger.info(f"{user} {user.username}, succesfully registered")
          flash('Registration successful! Please log in.', "succes")
          return redirect(url_for('login'))
        except Exception as e:
         app.logger.error(f"{user.username}, error while registering {e}")
    return render_template('register.html', form=form)

import os
from dotenv import load_dotenv
from flask_dance.contrib.google import make_google_blueprint, google

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=["profile", "email"]
)

app.register_blueprint(google_bp, url_prefix="/login")

@app.route('/login/google')
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", "error")
        return redirect(url_for("login"))
    user_info = resp.json()
    email = user_info.get("email")
    username = user_info.get("name") or (email.split("@")[0] if email else None)
    if not email or not username:
        flash("Google account missing email or username.", "error")
        return redirect(url_for("login"))
    user = User.query.filter_by(email=email).first()
    if not user:
        base_username = username
        count = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{count}"
            count += 1
        user = User(username=username, email=email)
        try: 
            db.session.add(user)
            db.session.commit()
            flash(f"Account created for {username} via Google login.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "error")
            return redirect(url_for("login"))   
    else:
        flash(f"Logged in as {user.username} via Google login.", "success")
    login_user(user)
    return redirect(url_for("index"))

from flask_dance.contrib.azure import make_azure_blueprint, azure

azure_bp = make_azure_blueprint(
    client_id="MICROSOFT_CLIENT_ID",
    client_secret="MICROSOFT_CLIENT_SECRET",
    redirect_to="azure_login",
    tenant="common"
)
app.register_blueprint(azure_bp, url_prefix="/login")

@app.route("/login/microsoft")
def microsoft_login():
    if not azure.authorized:
        return redirect(url_for("azure.login"))
    resp = azure.get("/v1.0/me")
    user_info = resp.json()
    # Use user_info["userPrincipalName"] to log in or register the user
    # Implement user lookup/creation logic here
    return redirect(url_for("index"))

@app.route('/logout')
@login_required
def logout():
    activity_logger.info(f"{current_user} {current_user.username}, logged out")
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    form = CSRFOnlyForm()
    if current_user.is_master or current_user.is_admin:
        challenges = Todo.query.all()
        app_status = app.config['APP_STATUS']
        users = User.query.all()
        return render_template('admin.html', challenges=challenges, users=users, app_status=app_status, form=form)
    
    if not current_user.is_authenticated:
        activity_logger.info(f"trying to acces admin panel without logging in")
        flash('Please log in first.')
        return redirect(url_for('login'))
    
    if not current_user.is_master or not current_user.is_admin:
        activity_logger.info(f"{current_user} {current_user.username}, tried to acces admin without permission")
        flash('You are not authorized to view this page.')
        return redirect(url_for('index'))
    return redirect(url_for('index'))

def get_log_content(log_file_path, num_lines=None):
    if not os.path.exists(log_file_path):
        return []
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
        if num_lines:
            return lines[-num_lines:] # Get the last N lines
        return lines

@app.route('/admin/logs')
@login_required
def view_logs():
    # Security: Only allow master or admin users to view logs
    if not (current_user.is_master or current_user.is_admin):
        flash('You are not authorized to this page.', 'error')
        activity_logger.warning(f"{current_user.username} (ID: {current_user.id}) attempted to access logs without authorization.")
        return redirect(url_for('index'))

    log_type = request.args.get('log_type', 'app_log') # Default to app_log
    filter_text = request.args.get('filter_text', '').strip()
    num_lines_str = request.args.get('num_lines', '50') # Default to 50 lines
    
    try:
        num_lines = int(num_lines_str) if num_lines_str else None
        if num_lines is not None and num_lines <= 0:
            num_lines = None # Treat non-positive as no limit
    except ValueError:
        num_lines = None # Invalid input, treat as no limit
        flash("Invalid number of lines specified. Showing all/default.", 'warning')

    log_file = None
    log_name = ""

    if log_type == 'app_log':
        log_file = 'logs/app.log'
        log_name = 'Application Log'
    elif log_type == 'upload_log':
        log_file = 'logs/upload.log'
        log_name = 'Upload Log'
    elif log_type == 'activity_log':
        log_file = 'logs/activity.log'
        log_name = 'Activity Log'
    elif log_type == 'error_log':
        log_file = 'logs/error.log'
        log_name = 'Error Log'
    else:
        flash('Invalid log type specified.', 'error')
        log_type = 'app_log' # Reset to default
        log_file = 'logs/app.log'
        log_name = 'Application Log'
        
    full_log_path = os.path.join(app.root_path, log_file)
    
    log_lines = get_log_content(full_log_path, num_lines)
    
    # Filter log lines
    filtered_log_lines = []
    if filter_text:
        search_pattern = re.compile(re.escape(filter_text), re.IGNORECASE) # Case-insensitive search
        for line in log_lines:
            if search_pattern.search(line):
                filtered_log_lines.append(line)
    else:
        filtered_log_lines = log_lines

    # Log access for auditing
    activity_logger.info(f"{current_user.username} (ID: {current_user.id}) accessed {log_name} with filter '{filter_text}' and lines '{num_lines_str}'.")

    return render_template('admin_logs.html',
        log_lines=filtered_log_lines,
        log_name=log_name,
        log_type=log_type,
        filter_text=filter_text,
        num_lines=num_lines_str,
        all_log_types=['app_log', 'upload_log', 'activity_log', 'error_log'])


@app.route('/admin/logs/download/<log_file_name>')
@login_required
def download_log(log_file_name):
    if not (current_user.is_master or current_user.is_admin):
        flash('You are not authorized to download logs.', 'error')
        activity_logger.warning(f"{current_user.username} (ID: {current_user.id}) attempted to download logs without authorization.")
        return redirect(url_for('index'))

    # Security: Ensure only valid log files can be downloaded
    allowed_log_files = ['app.log', 'upload.log', 'activity.log', 'error.log']
    if log_file_name not in allowed_log_files:
        flash('Invalid log file specified for download.', 'error')
        activity_logger.warning(f"{current_user.username} (ID: {current_user.id}) attempted to download invalid log file: {log_file_name}")
        return redirect(url_for('view_logs'))

    log_directory = os.path.join(app.root_path, 'logs')
    
    try:
        activity_logger.info(f"{current_user.username} (ID: {current_user.id}) downloaded log file: {log_file_name}")
        return send_from_directory(directory=log_directory, path=log_file_name, as_attachment=True)
    except FileNotFoundError:
        flash(f"Log file '{log_file_name}' not found.", 'error')
        error_logger.error(f"Download request for non-existent log file: {log_file_name}")
        return redirect(url_for('view_logs'))
    except Exception as e:
        flash(f"An error occurred during download: {str(e)}", 'error')
        error_logger.critical(f"Error downloading log file {log_file_name}: {e}")
        return redirect(url_for('view_logs'))
    
@app.route('/admin/send-email/', methods=["POST", "GET"])
@login_required
def admin_email():
    form = CSRFOnlyForm()
    # Authorization check FIRST
    if not (current_user.is_master or current_user.is_admin):
        activity_logger.info(f"{current_user} {current_user.username}, is trying to send an email without admin or master role")
        abort(403)

    if form.validate_on_submit():
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
            app.logger.info(f"Email with header {msg} and text {msg.body} sended to all users by {current_user} {current_user.username}")
            flash("Email sucesfully sent to all users.")
        except Exception as e:
            flash(f"Sending email failed. Error: {str(e)}", 'error')
            error_logger.error(f"Admin send email error: {e}")  # Log the error

    return render_template('admin_email.html', form=form)

    
@app.route('/admin/approve_challenge/<int:id>')
@login_required
def approve_challenge(id):
    if not (current_user.is_master or current_user.is_admin):
        activity_logger.info(f"{current_user} {current_user.username}, tried to aprove challenge without master or admin role")
        return redirect(url_for('index'))
    challenge = Todo.query.get_or_404(id)
    challenge.approved = True
    db.session.commit()
    app.logger.info(f"Admin approved challenge {challenge} {challenge.slug}")
    return redirect(url_for('admin'))

@app.route('/admin/delete_challenge/<int:id>')
@login_required
def delete_challenge(id):
    if not (current_user.is_master or current_user.is_admin):
        activity_logger.info(f"{current_user} {current_user.username}, tried to delete challenge without admin or master role")
        return redirect(url_for('index'))
    challenge = Todo.query.get_or_404(id)
    try:
        db.session.delete(challenge)
        db.session.commit()
        app.logger.info(f"Admin deleted challenge {challenge} {challenge.slug}")
    except Exception as e:
        flash("error deleting challenge")
        app.logger.error(f"Error deleting challenge {challenge} {e}")

    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<int:id>')
@login_required
def delete_user(id):
    
    user = User.query.get_or_404(id)

    if current_user.is_master:
        try:
            db.session.delete(user)
            db.session.commit()
            activity_logger.info(f"{current_user.username}, deleted user {user.userame}")
        except Exception as e:
            app.logger.error(f"Error deleting user {user} {user.username} {e}")
        return redirect(url_for('admin'))
    
    if not current_user.is_master or current_user.is_admin:
        activity_logger.info(f"{current_user} {current_user.username}, tried to delete user without admin or master role")
        return redirect(url_for('index'))
    if user.is_admin and not current_user.is_admin:
        if user.is_master:
            pass
        else:
            flash('Cannot delete admin users')
            activity_logger.info(f"{current_user} {current_user.username}, tried deleting {user}, and doesnt have permission")
            return redirect(url_for('admin'))
    try: 
      db.session.delete(user)
      db.session.commit()
      activity_logger.info(f"{current_user.username}, deleted user {user.userame}")
    except Exception as e:
        app.logger.error(f"Error deleting user {user} {user.username} {e}")
    return redirect(url_for('admin'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = CSRFOnlyForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST' and form.validate():
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
                app.logger.info(f"{email}, requested password reset link and email has been send")
            except Exception as e:
                flash(f'Failed to send email. Please try again later. Error: {str(e)}', 'error')
                db.session.rollback() # Rollback the token generation if email fails
                app.logger.error(f"Email sending error db rolled back: {e}") # Log the error for debugging
        else:
            # It's good practice not to reveal if an email exists for security reasons
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
            app.logger.info(f"Reset link sent to {email}")
        
        return redirect(url_for('login', form=form))
    
    return render_template('forgot.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = CSRFOnlyForm()
    if current_user.is_authenticated:
        app.logger.info(f"{current_user} {current_user.username}, already logged in")
        flash("already logged in")
        return redirect(url_for('index'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        app.logger.error(f"{token}, is invalid or expired for {user}")
        flash('That is an invalid or expired token.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST' and form.validate():
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            flash('Please enter both password and confirm password.', 'error')
            return render_template('reset_password.html', token=token, form=form)

        if password != confirm_password:
            app.logger.info(f"Passwords not matching for {user}")
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token, form=form)

        user.set_password(password)
        user.reset_token = None # Clear the token after successful reset
        user.reset_token_expiration = None # Clear the expiration
        db.session.commit()
        app.logger.info(f"Password for {user} {user.username}, succesfully reset")
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('reset.html', token=token, form=form)

@app.route('/reset_user_password/<int:id>', methods=['POST']) # Change to POST for better security
@login_required
def reset_user_password(id):
    # Only master users can reset passwords
    if not current_user.is_master:
        activity_logger.info(f"{current_user} {current_user.username}, tried to reset user password without master role")
        abort(403)

    user = User.query.get_or_404(id)

    # Prevent master admin from resetting their own password this way (or other admins)
    if user.is_master and user.id == current_user.id:
        activity_logger.info(f"Master tried to reset own password through master panel permission denied")
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
Maakplaats Team
"""

    try:
        mail.send(msg)
        db.session.commit() # Commit the token to the database after successful email sending
        activity_logger.info(f"Admin reseted password of {user.username} email send to {user.email}")
        flash(f"Password reset link sent to '{user.username}' ({user.email}). User must use the link to set a new password.", "info")
    except Exception as e:
        db.session.rollback() # Rollback the token generation if email fails
        flash(f"Failed to send password reset email to '{user.username}'. Error: {str(e)}", 'error')
        error_logger(f"Admin or master {current_user.username} forced reset email error: {e}") # Log the error for debugging

    return redirect(url_for('admin'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/forum')
def forum():
    form = CSRFOnlyForm()
    likeform = CSRFOnlyForm()
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
    return render_template('forum.html', likeform=likeform, form=form, tasks=tasks, sortfilter=sortfilter)

@app.route('/uploadtoforum', methods=['GET', 'POST'])
@login_required
def upload():
    form = CSRFOnlyForm()

    if request.method == 'POST' and form.validate():
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
            upload_logger.info(f"{current_user.username}, uploaded file {filename}")

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
            upload_logger.info(f"{current_user} {current_user.username}, uploaded new task {new_task}")
            if not (current_user.is_master or current_user.is_admin):
                app.logger.info(f"{current_user} {current_user.username}'s challenge {title}, is waiting for approval")
                flash("When your challenge gets approved, you'll see it here.", "info")
            return redirect('/forum')
        except IntegrityError as i:
            db.session.rollback()
            app.logger.error(f"A challenge with that slug already exists {i}")
            flash("A challenge with a similar slug already exists. Try a different title.", "danger")
            return render_template('uploadtoforum.html')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error adding challenge: {str(e)}")
            return 'There was an issue adding your challenge'
    else:
        app.logger.warning(f"Form validation failed. Errors: {form.errors}")
    return render_template('uploadtoforum.html', form=form)

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
            upload_logger.info(f"{current_user} {current_user.username}, liked {id}")
            liked_tasks.append(id)
        elif not liked and id in liked_tasks:
            upload_logger.info(f"{current_user} {current_user.username}, unliked {id}")
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
        app.logger.error(f"Error processing like {e}")
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
    from werkzeug.datastructures import CombinedMultiDict
    
    task = Todo.query.get_or_404(id)
    form = CSRFOnlyForm()
    delete = DeleteForm()
    
    # Check authorization
    if not (current_user.id == task.author_id or current_user.is_admin):
        activity_logger.info(f"Someone not authorized tried to update {task}")
        flash('You are not authorized to edit this challenge')
        return redirect(url_for('forum'))

    if request.method == 'GET':
        return render_template('update.html', form=form, task=task, sub_questions=task.get_sub_questions_list(), delete=delete)

    if request.method == 'POST' and form.validate():
        print(f"Updating task {id} by user {current_user.username}")  # Debug log
        
        # Update task fields
        task.title = request.form.get('title', '').strip()
        task.main_question = request.form.get('mainQuestion', '').strip()
        
        # Handle sub questions properly
        sub_questions_list = request.form.getlist('subQuestion[]')
        task.sub_questions = json.dumps([q.strip() for q in sub_questions_list if q.strip()])
        
        task.description = request.form.get('description', '').strip()
        task.end_product = request.form.get('endProduct', '').strip()
        task.category = request.form.get('categorie', '').strip()

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                # Create custom filename similar to upload route
                ext = file.filename.rsplit('.', 1)[1].lower()
                title_slug = slugify(task.title)
                timestamp = int(time.time())
                custom_filename = f"{current_user.username}_{title_slug}_{timestamp}.{ext}"
                filename = secure_filename(custom_filename)
                
                # Save the file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                task.image = filename
                upload_logger.info(f"{current_user.username}, updated image for task {task.id} with file {filename}")

        # Reset approval status if user is not admin/master
        if not (current_user.is_admin or current_user.is_master):
            task.approved = False  # Fixed: was Todo.challenge.approved

        try:
            db.session.commit()
            upload_logger.info(f"{current_user} {current_user.username}, updated challenge {task}")
            flash('Challenge updated successfully')
            return redirect(url_for('forum'))
        except Exception as e:
            app.logger.error(f"Error updating challenge: {str(e)}")
            db.session.rollback()
            flash('There was an issue updating your challenge')
            return redirect(url_for('forum'))
    else:
        # Log form validation errors for debugging
        if form.errors:
            app.logger.warning(f"Form validation failed for update. Errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'error')
    
    # If form doesn't validate, render the form again with errors
    return render_template('update.html', form=form, task=task, sub_questions=task.get_sub_questions_list(), delete=delete)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    # Get the task or return 404
    task_to_delete = Todo.query.get_or_404(id)
    
    # Check authorization
    if not (current_user.id == task_to_delete.author_id or current_user.is_admin):
        activity_logger.info(f"{current_user} {current_user.username}, tried to delete challenge {task_to_delete}")
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
        app.logger.info(f"Challenge {task_to_delete}, deleted succesfully")
        return redirect(url_for('forum'))
    except Exception as e:
        app.logger.error(f"Error deleting challenge {id}: {str(e)}")  # Debug logging
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
            upload_logger.info(f"{current_user} {current_user.username}, uploaded image {filename}")
        return redirect(url_for('/uploadtoforum'))
        
    return render_template('upload.html')

csrf.exempt(like)
csrf.exempt(like_status)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=False, ssl_context=("cert.pem", "key.pem"))