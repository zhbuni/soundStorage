from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class UploadSoundForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание')
    tags = StringField('Тэги, разделенные запятыми. Например: sad, piano, game')
    file = FileField(validators=[FileRequired(),
                                 FileAllowed(['mp3', 'wav'], 'Только аудио mp3 и wav!')])
    submit = SubmitField('Загрузить')
