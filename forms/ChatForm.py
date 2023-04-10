from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import BooleanField, SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired


class ChatForm(FlaskForm):
    message = StringField('Напишите сообщение', validators=[DataRequired()])
    submit = SubmitField('Отправить')
