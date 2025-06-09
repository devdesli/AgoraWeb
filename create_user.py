from app import app, db
from models import User

username = input("username\n")
email = input("email \n")
password = input("password\n")
with app.app_context():
    existing_user = User.query.filter_by(username=username).first()
    if not existing_user:
        user = User(username=username, email=email, is_admin=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(' user created successfully')
    else:
        print('user already exists')
