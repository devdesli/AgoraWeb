from flask import Blueprint, current_app, redirect, url_for
from flask_login import current_user
from flask_restful import Api, Resource
from models import User, db, Todo, TodoContributor
import requests as request

api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp)


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
