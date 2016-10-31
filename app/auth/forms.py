from flask_wtf import Form
from wtforms import StringField,BooleanField,SubmitField,PasswordField
from wtforms.validators import Required,Length,Email,Regexp,EqualTo,ValidationError
from ..models import User

class LoginForm(Form):
    email=StringField('Email',validators=[Required(),Length(1,64),Email()])
    password=PasswordField('Password',validators=[Required()])
    remember_me=BooleanField('Keep me logged in')
    submit=SubmitField('Log In')

class RegisterForm(Form):
    email=StringField('Email',validators=[Required(),Length(1,64),Email()])
    username=StringField('Username',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password=PasswordField('Password',validators=[Required(),EqualTo('password2',message='Password must match')])
    password2=PasswordField('Confirm your password',validators=[Required()])
    submit=SubmitField('Register')

    def verify_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

    def verify_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already registeredwd')

class ChangePasswordForm(Form):
    old_password=PasswordField('Old Password',validators=[Required()])
    password=PasswordField('New Password',validators=[Required(),EqualTo('password2',message='The password must match')])
    password2=PasswordField('Confirm your password',validators=[Required()])
    submit=SubmitField('Update your password')

class PasswordResetRequestForm(Form):
    email=StringField('Email',validators=[Required(),Length(1,64),Email()])
    submit=SubmitField('Reset Password')

class PasswordResetForm(Form):
    email=StringField('Email',validators=[Required(),Length(1,64),Email()])
    password=PasswordField('password',validators=[Required(),EqualTo('password2',message='The password must match')])
    password2=PasswordField('Confirm your password',validators=[Required()])
    submit=SubmitField('Reset Password')

    def validate_email(self,field):
         if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')

class ChangeEmailForm(Form):
    email=StringField('Email',validators=[Required(),Length(1,64),Email()])
    password=PasswordField('Password',validators=[Required()])
    submit=SubmitField('Update Email Address')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')