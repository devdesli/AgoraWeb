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
    title = TextAreaField("Titel", validators=[DataRequired(), Length(max=70)])
    description = TextAreaField("Informatie", validators=[DataRequired(), Length(max=100)])
    mainQuestion = TextAreaField("Hoofdvraag", validators=[DataRequired(), Length(max=60)])
    # subQuestions handled manually in HTML — no need to define them here
    endProduct = TextAreaField("Eindproduct", validators=[DataRequired()])
    categorie = SelectField("Categorie", choices=[
        ("Aardrijkskunde", "Aardrijkskunde"),
        ("Biologie", "Biologie"),
        ("Informatica", "Informatica"),
        ("Economie", "Economie"),
        ("Natuurkunde", "Natuurkunde"),
        ("Maatschappijleer", "Maatschappijleer"),
        ("Lichamelijke opvoeding", "Lichamelijke opvoeding"),
        ("Kunst en Cultuur", "Kunst en Cultuur"),
        ("Wiskunde", "Wiskunde"),
        ("Geschiedenis", "Geschiedenis"),
        ("Engels", "Engels"),
        ("Spaans", "Spaans"),
        ("Nederlands", "Nederlands"),
        ("Frans", "Frans"),
        ("Duits", "Duits"),
        ("Handvaardigheid", "Handvaardigheid"),
        ("Muziek", "Muziek"),
        ("Scheikunde", "Scheikunde"),
        ("Overig", "Overig"),
    ], validators=[DataRequired()])

    image = FileField("Afbeelding", validators=[FileAllowed(["jpg", "jpeg", "png", "gif"], "Alleen afbeeldingen toegestaan")])

class UploadForm(FlaskForm):
    title = TextAreaField(validators=[DataRequired(), Length(max=30)])
    mainQuestion = TextAreaField(validators=[DataRequired(), Length(max=60)])  # Fixed name
    description = TextAreaField(validators=[DataRequired(), Length(max=100)])
    endProduct = TextAreaField(validators=[DataRequired()])  # Fixed name
    categorie = SelectField("Categorie", choices=[
        ("", "Selecteer een categorie"),  # Added empty option
        ("Aardrijkskunde", "Aardrijkskunde"),
        ("Biologie", "Biologie"),
        ("Informatica", "Informatica"),
        ("Economie", "Economie"),
        ("Natuurkunde", "Natuurkunde"),
        ("Maatschappijleer", "Maatschappijleer"),
        ("Lichamelijke opvoeding", "Lichamelijke opvoeding"),
        ("Kunst en Cultuur", "Kunst en Cultuur"),
        ("Wiskunde", "Wiskunde"),
        ("Geschiedenis", "Geschiedenis"),
        ("Engels", "Engels"),
        ("Spaans", "Spaans"),
        ("Nederlands", "Nederlands"),
        ("Frans", "Frans"),
        ("Duits", "Duits"),
        ("Handvaardigheid", "Handvaardigheid"),
        ("Muziek", "Muziek"),
        ("Scheikunde", "Scheikunde"),
        ("Overig", "Overig"),
    ], validators=[DataRequired()])
    # Fixed image field - this should match your HTML
    image = FileField("Afbeelding", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], "Alleen afbeeldingen toegestaan")])

class LikeForm(FlaskForm):
    pass

class ResetUserBtnForm(FlaskForm):
    pass