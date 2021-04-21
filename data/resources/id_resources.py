import json

from flask import request
from flask_restful import Resource

from .. import db_session
from .. import tags
from ..sounds import Sound


class IdsResource(Resource):
    def get(self):
        session = db_session.create_session()
        cont = {}
        # По дефолту поиск происходит по названию
        if request.args.get('searchtype') and request.args.get('searchtype') in ('tag', 'title'):
            search_type = request.args.get('searchtype')
        else:
            search_type = 'title'

        if request.args.get('query'):
            query_str = request.args.get('query')
            if search_type == 'title':
                sound_id = session.query(Sound.name, Sound.id).filter(Sound.name == query_str).all()
            else:
                sound_id = session.query(Sound.name, Sound.id).join(tags.Tag,
                                                                    Sound.tags).filter(
                    tags.Tag.name.like('%{}%'.format(query_str))).all()
        else:
            sound_id = session.query(Sound.name, Sound.id).all()
        for el in sound_id:
            if el[0] not in cont:
                cont[el[0]] = [el[1]]
            else:
                cont[el[0]] += [el[1]]
        return json.dumps(cont)
