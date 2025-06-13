from app import app, db
from models import User

with app.app_context():
    username = input("input the username you want to make ADMIN!")
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_admin = True
        user.is_master = False
        db.session.commit()
        print(f'User {user.username} is now an ADMIN!')
    else:
        print({username} + 'not found')
