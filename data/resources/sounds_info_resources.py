from .. import db_session
from ..sounds import Sound
from flask import jsonify
from flask_restful import Resource
from .. import tags
from .. import comments
import base64
import json
import os


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
