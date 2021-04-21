import json
from .. import db_session
from ..sounds import Sound
from flask import jsonify, request
from flask_restful import Resource
from .. import tags
from .. import sounds
from .. import comments
from flask_jwt_extended import jwt_required, get_jwt_identity
import base64
import os


# по саундФайлу извлекает из БД сам файл звука, кодирует в base64 и возвращает json с ним
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

        filepath = os.path.join('static', 'sounds', '{}.mp3'.format(filename))
        f = open(filepath, 'wb')
        s = base64.decodebytes(bytes(content, encoding='utf-8'))
        f.write(s)
        f.close()
        if not is_mp3_valid(filepath):
            return jsonify({'error': 'Wrong content'})
        sound = sounds.Sound(name=title,
                             filename=filename,
                             description=description,
                             author_id=current_user)
        db_sess.add(sound)
        db_sess.commit()



def is_mp3_valid(file_path):
    is_valid = False
    f = open(file_path, 'r')
    block = f.read(1024)
    frame_start = block.find(chr(255))
    block_count = 0  # abort after 64k
    while len(block) > 0 and frame_start == -1 and block_count < 64:
        block = f.read(1024)
        frame_start = block.find(chr(255))
        block_count += 1

    if frame_start > -1:
        frame_hdr = block[frame_start:frame_start + 4]
        is_valid = frame_hdr[0] == chr(255)

        mpeg_version = ''
        layer_desc = ''
        uses_crc = False
        bitrate = 0
        sample_rate = 0
        padding = False
        frame_length = 0

        if is_valid:
            is_valid = ord(frame_hdr[1]) & 0xe0 == 0xe0  # validate the rest of the frame_sync bits exist

        if is_valid:
            if ord(frame_hdr[1]) & 0x18 == 0:
                mpeg_version = '2.5'
            elif ord(frame_hdr[1]) & 0x18 == 0x10:
                mpeg_version = '2'
            elif ord(frame_hdr[1]) & 0x18 == 0x18:
                mpeg_version = '1'
            else:
                is_valid = False

        if is_valid:
            if ord(frame_hdr[1]) & 6 == 2:
                layer_desc = 'Layer III'
            elif ord(frame_hdr[1]) & 6 == 4:
                layer_desc = 'Layer II'
            elif ord(frame_hdr[1]) & 6 == 6:
                layer_desc = 'Layer I'
            else:
                is_valid = False

        if is_valid:
            uses_crc = ord(frame_hdr[1]) & 1 == 0

            bitrate_chart = [
                [0, 0, 0, 0, 0],
                [32, 32, 32, 32, 8],
                [64, 48, 40, 48, 16],
                [96, 56, 48, 56, 24],
                [128, 64, 56, 64, 32],
                [160, 80, 64, 80, 40],
                [192, 96, 80, 96, 40],
                [224, 112, 96, 112, 56],
                [256, 128, 112, 128, 64],
                [288, 160, 128, 144, 80],
                [320, 192, 160, 160, 96],
                [352, 224, 192, 176, 112],
                [384, 256, 224, 192, 128],
                [416, 320, 256, 224, 144],
                [448, 384, 320, 256, 160]]
            bitrate_index = ord(frame_hdr[2]) >> 4
            if bitrate_index == 15:
                is_valid = False
            else:
                bitrate_col = 0
                if mpeg_version == '1':
                    if layer_desc == 'Layer I':
                        bitrate_col = 0
                    elif layer_desc == 'Layer II':
                        bitrate_col = 1
                    else:
                        bitrate_col = 2
                else:
                    if layer_desc == 'Layer I':
                        bitrate_col = 3
                    else:
                        bitrate_col = 4
                bitrate = bitrate_chart[bitrate_index][bitrate_col]
                is_valid = bitrate > 0

        if is_valid:
            sample_rate_chart = [
                [44100, 22050, 11025],
                [48000, 24000, 12000],
                [32000, 16000, 8000]]
            sample_rate_index = (ord(frame_hdr[2]) & 0xc) >> 2
            if sample_rate_index != 3:
                sample_rate_col = 0
                if mpeg_version == '1':
                    sample_rate_col = 0
                elif mpeg_version == '2':
                    sample_rate_col = 1
                else:
                    sample_rate_col = 2
                sample_rate = sample_rate_chart[sample_rate_index][sample_rate_col]
            else:
                is_valid = False

        if is_valid:
            padding = ord(frame_hdr[2]) & 1 == 1

            padding_length = 0
            if layer_desc == 'Layer I':
                if padding:
                    padding_length = 4
                frame_length = (12 * bitrate * 1000 / sample_rate + padding_length) * 4
            else:
                if padding:
                    padding_length = 1
                frame_length = 144 * bitrate * 1000 / sample_rate + padding_length
            is_valid = frame_length > 0

            if (frame_start + frame_length < len(block)):
                is_valid = block[frame_start + frame_length] == chr(255)
            else:
                offset = (frame_start + frame_length) - len(block)
                block = f.read(1024)
                if len(block) > offset:
                    is_valid = block[offset] == chr(255)
                else:
                    is_valid = False

    f.close()
    return is_valid



