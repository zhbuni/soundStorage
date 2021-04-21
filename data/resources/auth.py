import datetime

from flask import jsonify
from flask import request
from flask_jwt_extended import create_access_token
from flask_restful import Resource

from .. import db_session
from ..users import User


class RegisterResource(Resource):
    def post(self):
        db_sess = db_session.create_session()

        body = request.get_json()

        if 'password' not in body or 'email' not in body or 'nickname' not in body:
            return jsonify({'error': 'Bad request'})

        if db_sess.query(User).filter(
                User.nickname == body['nickname']).first() or db_sess.query(User).filter(
            User.email == body['email']).first():
            return jsonify({'error': 'User already exists'})

        user = User()
        user.nickname = body['nickname']
        user.email = body['email']
        user.set_password(body['password'])

        if 'profile_description' in body:
            user.profile_description = body['profile_description']

        user.image = 'picture.jpg'
        db_sess.add(user)
        db_sess.commit()

        return jsonify({'id': str(user.id)})


class LoginResource(Resource):
    def post(self):
        db_sess = db_session.create_session()

        body = request.get_json()

        if 'password' not in body or 'email' not in body:
            return jsonify({'error': 'Bad request'})

        user = db_sess.query(User).filter(User.email == body['email']).first()
        authorized = user.check_password(body['password'])

        if not authorized:
            return {'error': 'Email or password invalid'}

        expires = datetime.timedelta(days=7)
        access_token = create_access_token(identity=str(user.id), expires_delta=expires)
        return {'token': access_token}
