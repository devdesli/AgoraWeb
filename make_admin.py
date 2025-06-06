from app import app, db
from models import User

with app.app_context():
    username = input("input the username you want to make admin!")
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f'User {user.username} is now an admin')
    else:
        print({username} + 'not found')
