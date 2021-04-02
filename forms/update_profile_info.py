from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class UpdateProfileInfoForm(FlaskForm):
    nickname = StringField('Имя', validators=[DataRequired()])
    profile_description = TextAreaField('Описание профиля')
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль')
    password_again = PasswordField('Пароль еще раз')
    file = FileField('Аватар', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Только фото png и jpg!')])
    delete_profile_picture = SubmitField('Удалить аватарку')
    submit = SubmitField('Сохранить')
