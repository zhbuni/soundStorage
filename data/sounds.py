import sqlalchemy
from .db_session import SqlAlchemyBase, create_session
from sqlalchemy import orm
import datetime
from sqlalchemy_serializer import SerializerMixin
from .tags import Tag


class Sound(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'sounds'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    filename = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    downloads = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    datetime = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    user = orm.relation('User')
    tags = orm.relation("Tag",
                        secondary="association",
                        backref="sounds")

    def set_tags(self, tag_string, db_sess):
        self.tags.clear()
        tags = tag_string.strip()
        if tags:
            tags = set([i.strip() for i in tags.split(',')])
            for tagname in tags:
                if tagname:
                    tag = db_sess.query(Tag).filter(Tag.name == tagname.strip()).first()
                    # если такой тэг уже существует в бд, то не нужно создавать новый
                    if tag:
                        self.tags.append(tag)
                    # если такого тэга нет, то создаем новый
                    elif not tag:
                        self.tags.append(Tag(name=tagname.strip()))
