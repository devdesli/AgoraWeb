import os
from auth0_server_python.auth_server.server_client import ServerClient
from dotenv import load_dotenv
from extensions import db
from models import Auth0State, Auth0Transaction
from flask import current_app
import pickle

load_dotenv()

# Database-backed stores
class DBStateStore:
    """Database-backed state store for Auth0 sessions"""
    
    async def get(self, key, options=None):
        with current_app.app_context():
            record = Auth0State.query.filter_by(key=key).first()
            if record:
                return pickle.loads(record.value)
            return None
    
    async def set(self, key, value, options=None):
        with current_app.app_context():
            record = Auth0State.query.filter_by(key=key).first()
            if record:
                record.value = pickle.dumps(value)
            else:
                record = Auth0State(key=key, value=pickle.dumps(value))
                db.session.add(record)
            db.session.commit()
    
    async def delete(self, key, options=None):
        with current_app.app_context():
            record = Auth0State.query.filter_by(key=key).first()
            if record:
                db.session.delete(record)
                db.session.commit()
    
    async def delete_by_logout_token(self, claims, options=None):
        # For backchannel logout support
        pass

class DBTransactionStore:
    """Database-backed transaction store for OAuth flows"""
    
    async def get(self, key, options=None):
        with current_app.app_context():
            record = Auth0Transaction.query.filter_by(key=key).first()
            if record:
                return pickle.loads(record.value)
            return None
    
    async def set(self, key, value, options=None):
        with current_app.app_context():
            record = Auth0Transaction.query.filter_by(key=key).first()
            if record:
                record.value = pickle.dumps(value)
            else:
                record = Auth0Transaction(key=key, value=pickle.dumps(value))
                db.session.add(record)
            db.session.commit()
    
    async def delete(self, key, options=None):
        with current_app.app_context():
            record = Auth0Transaction.query.filter_by(key=key).first()
            if record:
                db.session.delete(record)
                db.session.commit()

# Initialize stores
state_store = DBStateStore()
transaction_store = DBTransactionStore()

# Initialize the Auth0 ServerClient
auth0 = ServerClient(
    domain=os.getenv('AUTH0_DOMAIN'),
    client_id=os.getenv('AUTH0_CLIENT_ID'),
    client_secret=os.getenv('AUTH0_CLIENT_SECRET'),
    secret=os.getenv('AUTH0_SECRET'),
    redirect_uri=os.getenv('AUTH0_REDIRECT_URI'),
    state_store=state_store,
    transaction_store=transaction_store,
    authorization_params={
        'scope': 'openid profile email',
        'audience': os.getenv('AUTH0_AUDIENCE', '')  # Optional: for API access
    }
)