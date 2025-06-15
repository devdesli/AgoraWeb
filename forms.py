from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField # Removed FieldList, FormField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileAllowed # Only FileAllowed is needed for validation here
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField(validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(validators=[DataRequired(), EqualTo('password', message='Passwords must match')])

class ForgotForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])

class ResetForm(FlaskForm):
    password = PasswordField(validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(validators=[DataRequired(), EqualTo('password', message='Passwords must match')])

class DeleteForm(FlaskForm):
    pass

class AdminEmailForm(FlaskForm):
    subject = StringField(validators=[DataRequired(), Length(max=200)])
    input_text = StringField(validators=[DataRequired()])

# Your HTML directly uses 'name' attributes matching these.
# We're removing the FieldList for subQuestion and FileField for image
# because your HTML structure doesn't align with how WTForms automatically renders them.
class UploadToForumForm(FlaskForm):
    pass
class UploadForm(FlaskForm):
    pass
class LikeForm(FlaskForm):
    pass

class ResetUserBtnForm(FlaskForm):
    pass

class CSRFOnlyForm(FlaskForm):
    pass