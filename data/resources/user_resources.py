from flask import jsonify
from .. import db_session
from ..users import User
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

from PIL import Image
import base64
from io import BytesIO
import os


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

    def get(self, user_id):
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == user_id).first()
        if user:
            content = dict()
            content['nickname'] = user.nickname
            content['profile_description'] = user.profile_description
            content['registration_date'] = '-'.join(map(str, (user.registration_date.year,
                                                              user.registration_date.month,
                                                              user.registration_date.day,
                                                              user.registration_date.hour,
                                                              user.registration_date.minute,
                                                              user.registration_date.second)))

            scriptDir = os.path.dirname(__file__)

            with open(os.path.join(scriptDir, '../../static/images/{}'.format(user.image)), mode='rb') as file:
                img = file.read()
            content['image'] = base64.encodebytes(img).decode('utf-8')
            return jsonify(content)
        else:
            return jsonify({'error': 'user not found'})
