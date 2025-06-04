We wanted to make it possible to share challenges with other people on a forum so we created this forum for that purpose.
To share with the community what you created
You can make an account and post a new challenge on the forum, update it, and delete it.

🤔 I’m looking for help with the design if anybody has tips just contact me with the info under here.

📫 How to reach me: Send an e-mail to my github e-mail see able on my account. 

This isn't finished and will probaly keep being updated in the future.

setup 
make a new folder to store the project 
then make an venv by running 
python - venv venv
this names the venv folder venv you can change this if you want just remember to also change the name of the next command to the right folder.
venv/Scripts/activate to activate the virtual enviroment
to run

export FLASK_APP=app.py
flask run --host=0.0.0.0


$env:FLASK_APP = "app.py"
flask shell


from models import User, db
admin = User.query.filter_by(username='admin').first()
if not admin:
    admin = User(username='admin', email='admim@gmail.com', is_admin=True)
    admin.set_password('admin')
    db.session.add(admin)
    db.session.commit()
