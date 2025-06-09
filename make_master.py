from app import app, db
from models import User

with app.app_context():
    username = input("input the username you want to make MASTER!")
    user = User.query.filter_by(username=username).first()
    if user:
        user.is_master = True
        db.session.commit()
        print(f'User {user.username} is now an MASTER!!!!')
    else:
        print({username} + 'not found')
