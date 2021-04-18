from . import db_session
from .sounds import Sound
from flask import jsonify
from flask_restful import Resource
import base64
import json
from os import path


# по саундФайлу извлекает из БД сам файл звука, кодирует в base64 и возвращает json с ним
class SoundsResource(Resource):
    def get(self, sound_id):
        session = db_session.create_session()

        sound = session.query(Sound).filter(Sound.id == sound_id).first()
        if not sound:
            return jsonify({'error': 'Sound not found'})
        sound_file = open(path.join('static', 'sounds', sound.filename) , 'rb')
        cont = {'content': str(base64.b64encode(sound_file.read()))}
        return json.dumps(cont)
