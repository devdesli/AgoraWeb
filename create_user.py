from app import app, db
from models import User

with app.app_context():
    existing_user = User.query.filter_by(username='testuser').first()
    if not existing_user:
        user = User(username='testuser', email='test@example.com', is_admin=False)
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        print('Test user created successfully')
    else:
        print('Test user already exists')
