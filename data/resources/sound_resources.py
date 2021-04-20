from .. import db_session
from ..sounds import Sound
from flask import jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import base64
import json
import os


# по саундФайлу извлекает из БД сам файл звука, кодирует в base64 и возвращает json с ним
class SoundsResource(Resource):
    @jwt_required()
    def get(self, sound_id):
        session = db_session.create_session()
        sound = session.query(Sound).filter(Sound.id == sound_id).first()
        if not sound:
            return jsonify({'error': 'Not Found'})
        sound_file = open(os.path.join('static', 'sounds', sound.filename), 'rb')
        cont = {'content': str(base64.b64encode(sound_file.read()))}
        return json.dumps(cont)

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
