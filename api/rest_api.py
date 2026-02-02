from flask import Blueprint, current_app, redirect, url_for
from flask_restful import Api, Resource
from models import db, Todo

api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp)


class Hello(Resource):
    def get(self):
        return {'message': 'Hello, World!'}


class ContributorApprove(Resource):
    def get(self, token):
        """Approve contributor for a challenge using the approval token."""
        todo = Todo.query.filter_by(contributor_approval_token=token).first()
        if not todo:
            return {'error': 'Invalid or expired token'}, 404

        todo.contributor_approved = True
        todo.contributor_approval_token = None
        db.session.add(todo)
        db.session.commit()

        # Redirect to the challenge page (if frontend exists) or return JSON
        try:
            return redirect(url_for('fullcard', id=todo.id, slug=todo.slug))
        except Exception:
            return {'message': 'Contributor approved', 'todo_id': todo.id}


api.add_resource(Hello, '/hello')
api.add_resource(ContributorApprove, '/contributor/approve/<string:token>', endpoint='contributorapprove')
