import json

from flask import request
from flask_restful import Resource

from .. import db_session
from ..sounds import Sound


class IdsResource(Resource):
    def get(self):
        session = db_session.create_session()
        cont = {}
        if request.args.get('soundname'):
            sound_id = session.query(Sound.name, Sound.id).filter(Sound.name == request.args.get('soundname')).all()
        else:
            sound_id = session.query(Sound.name, Sound.id).all()
        for el in sound_id:
            if el[0] not in cont:
                cont[el[0]] = [el[1]]
            else:
                cont[el[0]] += [el[1]]
        return json.dumps(cont)
