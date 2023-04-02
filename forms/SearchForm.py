from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    label = StringField('Поиск', validators=[DataRequired()], default='')
    submit = SubmitField('Искать')
