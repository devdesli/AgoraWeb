from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from slugify import slugify
import json
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_master = db.Column(db.Boolean, default=False)
    challenges = db.relationship('Todo', backref='author', lazy=True, cascade='all, delete-orphan')
    reset_token = db.Column(db.String(128), nullable=True)
    reset_token_expiration = db.Column(db.DateTime(timezone=True), nullable=True) 

    def set_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiration = datetime.now(timezone.utc) + timedelta(hours=1) 
        db.session.add(self)
        db.session.commit()
        return self.reset_token

    def verify_reset_token(self, token):
        if self.reset_token is None or self.reset_token != token:
            return False

        if self.reset_token_expiration is None:
            return False
        
        loaded_expiration = self.reset_token_expiration.replace(tzinfo=timezone.utc)

        # Now compare the localized datetime to the current UTC datetime
        return loaded_expiration > datetime.now(timezone.utc) # Corrected comparison to >

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # dingen die op de kaart staan 
    slug = db.Column(db.String(120), unique=True)
    likes = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    main_question = db.Column(db.String(200), nullable=False)
    sub_questions = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    end_product = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    approved = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    
    def get_sub_questions_list(self):
        try:
            # Safely loads the JSON string into a Python list
            return json.loads(self.sub_questions) if self.sub_questions else []
        except json.JSONDecodeError:
            # Fallback for malformed JSON or if it's just a plain string
            return [self.sub_questions] if self.sub_questions else []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug and self.title:
            self.slug = slugify(self.title)
    
    def __repr__(self):
        return f'<Todo {self.id}>'

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)

    def __repr__(self):
        return f'<Image {self.filename}>'
