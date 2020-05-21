from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, HiddenField, IntegerField, SelectField, TextAreaField, SubmitField, DecimalField, DateTimeField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First name', validators=[DataRequired()])
    last_name = StringField('last name', validators=[DataRequired()])
    email = StringField('Email address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class AddContract(FlaskForm):
    initiator_user_id = SelectField(label='Initiator',coerce=int,default=1)
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    contractor_user_id = SelectField(label='Contractor',coerce=int,validators=[DataRequired()])
    contract_template_id = SelectField(label='Contract Type',coerce=int,validators=[DataRequired()])
    value = DecimalField(validators=[DataRequired()])
    duedate = DateTimeField(label="Duedate (1995-10-10 16:03)", format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit')
    approve = SubmitField('Approve contract')
    finalize = SubmitField('Finalize contract')
    contractor_approval = StringField('Approved by contractor')
    contractor_approval_timestamp = StringField('Date of contractor approval')
    is_deployed = StringField('Is contract deployed on blockchain')
    is_finalized = StringField('Is contract finalized')
    finalization_timestamp = StringField('Date of contract finalization')
    contract_id = IntegerField('Contract ID')
    contract_date_added = StringField('Document version date')

class Maketransfer(FlaskForm):
    eth_recipient_address = StringField('Etherum recipient address', validators=[DataRequired()])
    value = DecimalField(validators=[DataRequired()])
    submit = SubmitField('Post')

class OrderItemForm(FlaskForm):
    product_id = HiddenField(validators=[DataRequired()])
    quantity = IntegerField(validators=[DataRequired()])
    order_id = HiddenField()
    submit = SubmitField('Update')

class ItemForm(FlaskForm):
    product_id = HiddenField(validators=[DataRequired()])
    quantity = HiddenField(validators=[DataRequired()], default=1)

class AddAttachmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Attachment Description', validators=[DataRequired()])
    picture = FileField()
    filename = StringField('filename')
    contract_id = IntegerField('Contract ID')
    type_id = IntegerField('Type ID',default=1)
    submit = SubmitField('Submit')