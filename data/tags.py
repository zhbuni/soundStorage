import sqlalchemy
from .db_session import SqlAlchemyBase


association_table = sqlalchemy.Table(
    'association',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('sounds', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('sounds.id')),
    sqlalchemy.Column('tags', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('tags.id'))
)


class Tag(SqlAlchemyBase):
    __tablename__ = 'tags'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
