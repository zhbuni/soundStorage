from flask import jsonify
from .. import db_session
from ..users import User
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity


class UserResource(Resource):
    @jwt_required()
    def delete(self, user_id):
        if user_id == int(get_jwt_identity()):
            db_sess = db_session.create_session()
            db_sess.delete(db_sess.query(User).get(user_id))
            db_sess.commit()
            return jsonify({'success': '200'})
        else:
            return jsonify({'error': 'Action is Forbidden'})
