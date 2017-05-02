from keg_elements.forms import Form, form_validator
from wtforms.fields import (
    BooleanField,
    HiddenField,
    PasswordField,
    StringField,
)
from wtforms import validators


__all__ = [
    'make_change_password_form',
    'make_forgot_password_form',
    'make_email_login_field',
    'make_login_form',
    'make_reset_password_form',
]


def make_change_password_form(old_password_validators, new_password_validators):
    class ChangePasswordForm(Form):
        next = HiddenField()
        old_password = PasswordField(
            u'Old Password',
            validators=[validators.DataRequired()] + old_password_validators
        )
        new_password = PasswordField(
            u'New Password',
            validators=[validators.DataRequired()] + new_password_validators
        )
        retype_password = PasswordField(u'Retype New Password', validators=[
            validators.EqualTo('new_password', message=u'Passwords do not match')
        ])

    return ChangePasswordForm


def make_forgot_password_form(email_validator=lambda *a, **kw: None):
    class ForgotPasswordForm(Form):
        next = HiddenField()

        email = StringField(u'Your email address', validators=[
            validators.DataRequired(),
            validators.Email(),
            email_validator,
        ])

    return ForgotPasswordForm


def make_email_login_field(email_validator=None):
    vl = [
        validators.DataRequired(),
        validators.Email(),
    ]
    if email_validator is not None:
        vl.append(email_validator)
    return StringField(u'Email', validators=vl)


def make_login_form(password_validator, id_field, enable_remember_me=True):
    class LoginForm(Form):
        next = HiddenField()
        id = id_field

        password = PasswordField('Password', validators=[
            validators.DataRequired(),
        ])

        if enable_remember_me:
            remember_me = BooleanField('Remember me')

        @form_validator
        def _password_validator(self):
            password_validator(self)

    return LoginForm


def make_reset_password_form(password_validators=None):
    class ResetPasswordForm(Form):
        next = HiddenField()
        new_password = PasswordField(
            u'New Password',
            validators=[validators.DataRequired()] + (password_validators or []))
        retype_password = PasswordField(u'Retype New Password', validators=[
            validators.EqualTo('new_password', message=u'Passwords do not match'),
        ])

    return ResetPasswordForm


def make_lock_form():
    class LockForm(Form):
        next = HiddenField()
        password = PasswordField(
            u'Passsword', validators=[validators.DataRequired()])

    return LockForm


def bool_validator(pred, error_message):
    """Returns a simple WTForms validator that raises the given error message as a validation error
    IFF the given predicate function returns False on the field's value.
    """
    def validator(form, field):
        if not pred(field.data):
            raise validators.ValidationError(error_message)

    return validator
