from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class UpdateSoundForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание')
    tags = StringField('Тэги, разделенные запятыми. Например: sad, piano, game')
    submit = SubmitField('Сохранить')
