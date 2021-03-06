from flask_wtf import FlaskForm
from wtforms import SubmitField, TextField
from wtforms.validators import InputRequired


class CommentForm(FlaskForm):
    content = TextField('Комментарий', validators=[InputRequired()])
    submit = SubmitField('post')