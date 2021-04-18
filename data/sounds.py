import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
import datetime
from sqlalchemy_serializer import SerializerMixin


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


