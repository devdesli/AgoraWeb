# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()
socketio = SocketIO()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://", strategy="moving-window")