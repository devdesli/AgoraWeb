from app import app, db
from models import User

with app.app_context():
    username = input("input the username you want to make COACH!")
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_coach = True
        user.is_admin = False
        user.is_master = False
        db.session.commit()
        print(f'User {user.username} is now an Coach!')
    else:
        print({username} + 'not found')
