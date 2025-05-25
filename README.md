We wanted to make it possible to share challenges with other people on a forum so we created this forum for that purpose a multifunctional forum_address for Agora.


setup 

to run

scp -r c:\\Users\\desli\\Documents\\projects\\challengeforum desli@100.76.148.64:/home/desli/export FLASK_APP=app.py

export FLASK_APP=app.py
flask run --host=0.0.0.0


cd c:\Users\desli\Documents\projects\challengeforum
$env:FLASK_APP = "app.py"
flask shell


from models import User, db
admin = User.query.filter_by(username='admin').first()
if not admin:
    admin = User(username='admin', email='develloperdesli@gmail.com', is_admin=True)
    admin.set_password('develloperdesli')
    db.session.add(admin)
    db.session.commit()