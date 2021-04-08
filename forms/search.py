from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    choices = ['title', 'tag']
    select = SelectField('Search for sounds:', choices=choices)
    searchStr = StringField()
    submit = SubmitField('Поиск')