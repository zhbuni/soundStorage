from flask import jsonify, request
from .. import db_session
from ..users import User
from ..sounds import Sound
from ..comments import Comment
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity


class CommentsListResource(Resource):
    @jwt_required()
    def post(self):
        db_sess = db_session.create_session()
        body = request.get_json()

        if 'content' not in body or 'sound_id' not in body:
            return jsonify({'error': 'Bad Request'})

        sound = db_sess.query(Sound).get(body['sound_id'])
        if not sound:
            return jsonify({'error': 'Not Found'})

        user = db_sess.query(User).get(get_jwt_identity())
        comment = Comment(content=body['content'],
                          sound_id=body['sound_id'],
                          user_id=user.id)
        db_sess.add(comment)
        db_sess.commit()
        return jsonify({'success': '200', 'id': str(comment.id)})

    def get(self):
        db_sess = db_session.create_session()
        res = {'comments': []}
        comments = db_sess.query(Comment).all()
        for comment in comments:
            res['comments'].append({'id': comment.id,
                                    'content': comment.content,
                                    'datetime': comment.datetime,
                                    'sound_id': comment.sound_id,
                                    'user_id': comment.user_id})
        return jsonify(res)


class CommentResource(Resource):
    def get(self, comment_id):
        db_sess = db_session.create_session()
        comment = db_sess.query(Comment).get(comment_id)
        if not comment:
            return jsonify({'error': 'Not Found'})
        return jsonify({'comment': {
                                    'content': comment.content,
                                    'datetime': comment.datetime,
                                    'sound_id': comment.sound_id,
                                    'user_id': comment.user_id}})