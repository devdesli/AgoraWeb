from flask import Blueprint, current_app, redirect, url_for
from flask_login import current_user
from flask_restful import Api, Resource
from models import User, db, Todo, TodoContributor
import requests
from flask import Blueprint, jsonify
import requests as request

api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

SCOPES = [
    "User.Read",
    "Mail.Read",
    "Calendars.Read",
    "Files.Read",
]

m365 = Blueprint("m365", __name__, url_prefix="/m365")

def _graph(auth, endpoint: str, params: dict = None):
    """Make an authenticated Microsoft Graph API request."""
    token = auth.get_token_for_user(SCOPES)
    if not token or "access_token" not in token:
        return {"error": "No valid token, please log in again."}

    response = requests.get(
        f"{GRAPH_BASE}{endpoint}",
        headers={"Authorization": f"Bearer {token['access_token']}"},
        params=params or {},
    )
    response.raise_for_status()
    return response.json()

def register_m365_routes(auth):
    """
    Call this in app.py after creating your Auth instance.
    Example:
        from m365 import m365, register_m365_routes
        app.register_blueprint(m365)
        register_m365_routes(auth)
    """

    @m365.route("/me")
    @auth.login_required
    def me(*, context):
        """Return the signed-in user's profile."""
        data = _graph(auth, "/me")
        return jsonify({
            "name":  data.get("displayName"),
            "email": data.get("mail") or data.get("userPrincipalName"),
            "id":    data.get("id"),
            "job":   data.get("jobTitle"),
        })

    @m365.route("/emails")
    @auth.login_required
    def emails(*, context):
        """Return the latest 10 emails."""
        data = _graph(auth, "/me/messages", {
            "$top": 10,
            "$select": "subject,from,receivedDateTime,isRead",
            "$orderby": "receivedDateTime desc",
        })
        return jsonify(data.get("value", []))

    @m365.route("/calendar")
    @auth.login_required
    def calendar(*, context):
        """Return the next 10 calendar events."""
        data = _graph(auth, "/me/events", {
            "$top": 10,
            "$select": "subject,start,end,location,organizer",
            "$orderby": "start/dateTime asc",
        })
        return jsonify(data.get("value", []))

    @m365.route("/files")
    @auth.login_required
    def files(*, context):
        """Return root OneDrive files and folders."""
        data = _graph(auth, "/me/drive/root/children", {
            "$select": "name,size,lastModifiedDateTime,webUrl,folder,file",
        })
        return jsonify(data.get("value", []))

    @m365.route("/teams")
    @auth.login_required
    def teams(*, context):
        """Return the user's Microsoft Teams."""
        data = _graph(auth, "/me/joinedTeams", {
            "$select": "displayName,description,id",
        })
        return jsonify(data.get("value", []))
    
class Hello(Resource):
    def get(self):
        return {'message': 'Hello, World!'}

class ContributorApprove(Resource):
    def get(self, token):
        """Approve contributor for a challenge using the approval token."""
        assoc = TodoContributor.query.filter_by(approval_token=token).first()
        if not assoc:
            return {'error': 'Invalid or expired token'}, 404

        assoc.approved = True
        assoc.approval_token = None
        db.session.add(assoc)
        db.session.commit()

        # Redirect to the challenge page (if frontend exists) or return JSON
        try:
            return redirect(url_for('fullcard', id=assoc.todo_id, slug=assoc.todo.slug))
        except Exception:
            return {'message': 'Contributor approved', 'todo_id': assoc.todo_id}

class Admin_Stats(Resource):
    def get(self):
        if current_user.is_master or current_user.is_admin:
            link = "https://api.codetabs.com/v1/loc?github=DevDesli/AgoraWeb"
            """Return some admin statistics."""
            total_users = User.query.count()
            total_todos = Todo.query.count()
            total_likes = db.session.query(db.func.sum(Todo.likes)).scalar() or 0
            pending_contributors = db.session.query(TodoContributor).filter_by(approved=False).count()
            code_size = request.get(link).text
            return {
                'total_users': total_users,
                'total_todos': total_todos,
                'likes': total_likes,
                'pending_contributors': pending_contributors,
                'code_size': code_size
            }

api.add_resource(Admin_Stats, '/admin/stats', endpoint='adminstats')
api.add_resource(Hello, '/hello')
api.add_resource(ContributorApprove, '/contributor/approve/<string:token>', endpoint='contributorapprove')
