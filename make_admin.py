from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(username='develloperdesli').first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f'User {user.username} is now an admin')
    else:
        print('User not found')
