import binascii
import json
from .. import db_session
from ..sounds import Sound
from flask import jsonify, request
from flask_restful import Resource
from .. import tags
from .. import comments
from .. import sounds
from flask_jwt_extended import jwt_required, get_jwt_identity
import base64
import os
import eyed3


class SoundsDownloadResource(Resource):
    @jwt_required()
    def get(self, sound_id):
        session = db_session.create_session()
        sound = session.query(Sound).filter(Sound.id == sound_id).first()
        if not sound:
            return jsonify({'error': 'Not Found'})
        sound_file = open(os.path.join('static', 'sounds', sound.filename), 'rb')
        cont = dict()

        cont['content'] = str(base64.b64encode(sound_file.read()))

        return json.dumps(cont)


class SoundsResource(Resource):
    def get(self, sound_id):
        session = db_session.create_session()
        sound = session.query(Sound).filter(Sound.id == sound_id).first()
        if not sound:
            return jsonify({'error': 'Not Found'})
        cont = dict()
        tag = session.query(tags.Tag).join(tags.Tag,
                                           Sound.tags).filter(Sound.id == sound_id).all()

        sound_comments = session.query(comments.Comment).filter(comments.Comment.sound_id == sound_id).all()
        cont['comments'] = [{'id': comment.id,
                                    'content': comment.content,
                                    'datetime': comment.datetime,
                                    'sound_id': comment.sound_id,
                                    'user_id': comment.user_id} for comment in sound_comments]
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


class SoundsPostResource(Resource):
    @jwt_required()
    def post(self):
        db_sess = db_session.create_session()
        body = request.get_json()
        current_user = get_jwt_identity()
        title = body.get('title', None)
        filename = body.get('filename', None)
        description = body.get('description', None)
        content = body.get('content', None)

        if not title or not filename or not description or not content:
            return jsonify({'error': 'Wrong body'})

        if len(filename.split('.')) == 2 and filename.split('.')[1] not in ('mp3', 'wav'):
            return jsonify({'error': 'only mp3 or wav'})

        filepath = os.path.join('static', 'sounds', '{}'.format(filename))
        f = open(filepath, 'wb')
        try:
            s = base64.decodebytes(bytes(content, encoding='utf-8'))
        except binascii.Error:
            return jsonify({'error': 'wrong content. It should be encoded in base64'})
        f.write(s)
        f.close()
        if not eyed3.load(filepath):
            return jsonify({'error': 'Wrong content. Mp3 or wav only'})
        sound = sounds.Sound(name=title,
                             filename=filename,
                             description=description,
                             author_id=current_user)
        db_sess.add(sound)
        db_sess.commit()
