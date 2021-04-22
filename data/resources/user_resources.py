from flask import jsonify, request
from .. import db_session
from ..users import User
from ..functions import generate_random_string
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from PIL import Image, UnidentifiedImageError
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

    @jwt_required()
    def put(self, user_id):
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(user_id)
        if not user:
            return jsonify({'error': 'Not Found'})
        if user.id != int(get_jwt_identity()):
            return jsonify({'error': 'Action is Forbidden'})

        body = request.get_json()
        if not body or len({'nickname', 'profile_description', 'email', 'password',
                            'picture', 'delete_picture'}.intersection(set(body.keys()))) == 0:
            return jsonify({'error': 'Bad Request'})

        if 'nickname' in body:
            if db_sess.query(User).filter(User.nickname == body['nickname']).first():
                return jsonify({'error': 'User already exists'})
            user.nickname = body['nickname']

        if 'email' in body:
            if db_sess.query(User).filter(User.email == body['email']).first():
                return jsonify({'error': 'User already exists'})
            user.email = body['email']

        if 'profile_description' in body:
            user.profile_description = body['profile_description']

        if 'password' in body:
            user.set_password(body['password'])

        if 'picture' in body and 'delete_picture' in body:
            return jsonify({'error': 'Bad Request'})

        if 'picture' in body and 'filename' in body['picture'] and 'content' in body['picture']:
            s = base64.decodebytes((bytes(body['picture']['content'], encoding='utf-8')))
            try:
                file_format = body['picture']['filename'].split('.')[-1]
                if file_format not in ['jpg', 'png', 'jpeg']:
                    raise UnidentifiedImageError()

                scriptDir = os.path.dirname(__file__)

                filename = generate_random_string(9) + '.' + file_format
                Image.open(BytesIO(s)).save(os.path.join(scriptDir, '../../static/images/{}'.format(filename)))
                user.image = filename
            except UnidentifiedImageError:
                return jsonify({'error': 'Unidentified Image'})
            except IndexError:
                return jsonify({'error': 'Invalid filename'})

        if 'delete_picture' in body and body['delete_picture']:
            if user.image != 'default-profile-picture.jpg':
                os.remove(os.path.join('static', 'images', user.image))
                user.image = 'default-profile-picture.jpg'

        db_sess.commit()
        return jsonify({'success': '200'})
