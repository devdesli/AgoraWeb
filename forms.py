from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField # Removed FieldList, FormField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileAllowed # Only FileAllowed is needed for validation here

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
    title = StringField(validators=[DataRequired(), Length(max=70)]) # Match HTML maxlength
    description = StringField(validators=[DataRequired(), Length(max=100)]) # Match HTML maxlength
    mainQuestion = StringField(validators=[DataRequired(), Length(max=60)]) # Match HTML maxlength
    # subQuestion is *not* a FieldList in the form definition here.
    # We will handle it as request.form.getlist('subQuestion[]') in the route.
    # We'll still add a placeholder StringField for basic validation if needed,
    # but the primary validation will be manual in the route or it'll pass
    # if at least one 'subQuestion[]' is present.
    # For a "required" check on subQuestions, we'll do it manually in the route.
    subQuestion = StringField(validators=[]) # Placeholder for validation messages, not functional for FieldList
    
    endProduct = StringField(validators=[DataRequired()]) # No maxlength in HTML, consider adding one
    categorie = StringField(validators=[DataRequired()]) # Select dropdown handles validation

    # No FileField here because you're using a direct <input type="file" name="image">
    # We'll use FileAllowed validator manually in the route for the uploaded file.
    # This dummy field allows passing `FileAllowed` validator errors to the template if you rendered them
    # But for strict "no HTML changes", you'll need to flash messages for file errors.
    image_dummy = StringField(validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif'], 'Images only! (PNG, JPG, JPEG, GIF)')])

class UploadForm(FlaskForm):
    title = StringField(validators=[DataRequired()])
    main_question = StringField(validators=[DataRequired()])
    sub_questions = StringField(validators=[DataRequired()]) # This is just a single string field, not a list
    description = StringField(validators=[DataRequired()])
    end_product = StringField(validators=[DataRequired()])
    category = StringField(validators=[DataRequired()])
    

class LikeForm(FlaskForm):
    pass

class ResetUserBtnForm(FlaskForm):
    pass