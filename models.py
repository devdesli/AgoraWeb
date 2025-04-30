from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import sqlalchemy as sa


db = SQLAlchemy()

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    # dingen die op de kaart staan 
    likes = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    main_question = db.Column(db.String(200), nullable=False)
    sub_questions = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    end_product = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(50), nullable=False)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Image {self.filename}>'

    def __repr__(self):
        return f'<Todo {self.id}>'
