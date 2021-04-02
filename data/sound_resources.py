from . import db_session
from .sounds import Sound
from flask import abort, jsonify
from flask_restful import Resource
import base64
import json


# по саундФайлу извлекает из БД сам файл звука, кодирует в base64 и возвращает json с ним
class SoundsResource(Resource):
    def get(self, sound_name):
        session = db_session.create_session()
        sound = session.query(Sound).filter(Sound.filename == sound_name)
        if not sound:
            return jsonify({'error': 'Sound not found'})
        sound_file = open(sound.filename, 'rb')
        cont = {'content': str(base64.b64encode(sound_file.read()))}
        return json.dumps(cont)
