import base64
import os

from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from .. import comments
from .. import db_session
from .. import tags
from ..sounds import Sound


# по саундФайлу извлекает из БД сам файл звука, кодирует в base64 и возвращает json с ним
class SoundsResource(Resource):
    @jwt_required()
    def get(self, sound_id):
        session = db_session.create_session()
        sound = session.query(Sound).filter(Sound.id == sound_id).first()
        if not sound:
            return jsonify({'error': 'Not Found'})
        sound_file = open(os.path.join('static', 'sounds', sound.filename), 'rb')
        cont = dict()

        cont['content'] = str(base64.b64encode(sound_file.read()))

        return jsonify(cont)



class SoundsInfoResource(Resource):
    def get(self, sound_id):
        session = db_session.create_session()
        sound = session.query(Sound).filter(Sound.id == sound_id).first()
        if not sound:
            return jsonify({'error': 'Not Found'})
        cont = dict()
        tag = session.query(tags.Tag).join(tags.Tag,
                                           Sound.tags).filter(Sound.id == sound_id).all()

        comment = session.query(comments.Comment).filter(comments.Comment.sound_id == sound_id).all()
        cont['comments'] = [com.content for com in comment]
        cont['tags'] = [tg.name for tg in tag]
        cont['name'] = sound.name
        cont['description'] = sound.description
        cont['author_id'] = sound.author_id
        cont['name'] = sound.name
        cont['created_date'] = '-'.join(map(str, (sound.datetime.year,
                                                  sound.datetime.month,
                                                  sound.datetime.day,
                                                  sound.datetime.hour,
                                                  sound.datetime.minute,
                                                  sound.datetime.second)))

        return jsonify(cont)

    @jwt_required()
    def delete(self, sound_id):
        db_sess = db_session.create_session()
        sound = db_sess.query(Sound).get(sound_id)
        if sound:
            if sound.author_id != int(get_jwt_identity()):
                return jsonify({'error': 'Action is Forbidden'})
            else:
                os.remove(os.path.join('static', 'sounds', sound.filename))
                db_sess.delete(sound)
                db_sess.commit()
                return jsonify({'success': '200'})
        else:
            return jsonify({'error': 'Not Found'})

    @jwt_required()
    def put(self, sound_id):
        db_sess = db_session.create_session()
        sound = db_sess.query(Sound).get(sound_id)
        if not sound:
            return jsonify({'error': 'Not Found'})
        if sound.author_id != int(get_jwt_identity()):
            return jsonify({'error': 'Action is Forbidden'})

        body = request.get_json()
        if not body or len({'name', 'description', 'tags'}.intersection(set(body.keys()))) == 0:
            return jsonify({'error': 'Bad Request'})

        if 'name' in body:
            sound.name = body['name']
        if 'description' in body:
            sound.description = body['description']
        if 'tags' in body and type(body['tags']) == list and body['tags']:
            sound.set_tags(', '.join(body['tags']), db_sess)
        elif 'tags' in body:
            return jsonify({'error': 'Bad Request'})

        db_sess.commit()
        return jsonify({'success': '200'})