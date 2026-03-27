# email server config 
import os
from dotenv import load_dotenv
from pathlib import Path

basedir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=basedir / '.env')

class Config:
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')  # This is crucial!
    APP_STATUS = os.getenv('APP_STATUS')
    
    # Microsoft 365 / Azure AD Configuration for Quadraam Tenet
    AZURE_OAUTH_CLIENT_ID = os.getenv('AZURE_OAUTH_CLIENT_ID')
    AZURE_OAUTH_CLIENT_SECRET = os.getenv('AZURE_OAUTH_CLIENT_SECRET')
    AZURE_OAUTH_TENANT = os.getenv('AZURE_OAUTH_TENANT', 'common')
    
    # OAuth Configuration
    AUTHORITY = os.getenv('AUTHORITY')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')
    # Flask Session Configuration
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'flask_sessions'