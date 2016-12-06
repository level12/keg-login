import flask
from werkzeug.datastructures import MultiDict
from wtforms import validators, fields

from keg_login.forms import make_change_password_form, make_forgot_password_form, make_login_form, \
    make_email_login_field, make_reset_password_form, bool_validator

app = flask.Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False


class TestChangePasswordForm(object):
    def form_cls(self, old_pw_validators=None, new_pw_validators=None):
        return make_change_password_form(old_pw_validators or [], new_pw_validators or [])

    def test_ok(self):
        with app.test_request_context():
            data = {
                'old_password': '12345',
                'new_password': 'password',
                'retype_password': 'password'
            }
            form = self.form_cls()(MultiDict(data))
            assert form.validate()

    def test_required(self):
        with app.test_request_context():
            form = self.form_cls()()
            assert not form.validate()
            msg = ['This field is required.']
            assert form.old_password.errors == msg
            assert form.new_password.errors == msg
            assert form.retype_password.errors == []

    def test_retype_validation(self):
        with app.test_request_context():
            data = {
                'old_password': '12345',
                'new_password': 'password',
                'retype_password': 'passw0rd'
            }
            form = self.form_cls()(MultiDict(data))
            assert not form.validate()
            assert form.old_password.errors == []
            assert form.new_password.errors == []
            assert form.retype_password.errors == ['Passwords do not match']

    def test_extra_validators(self):
        with app.test_request_context():
            data = {
                'old_password': '12345',
                'new_password': 'password',
                'retype_password': 'password'
            }
            form = self.form_cls(
                old_pw_validators=[validators.Length(max=3)],
                new_pw_validators=[validators.Email()]
            )(MultiDict(data))

            assert not form.validate()
            assert form.old_password.errors == ['Field cannot be longer than 3 characters.']
            assert form.new_password.errors == ['Invalid email address.']
            assert form.retype_password.errors == []


class TestForgotPasswordForm(object):
    def form_cls(self, email_validator=lambda *a, **kwargs: None):
        return make_forgot_password_form(email_validator)

    def test_ok(self):
        with app.test_request_context():
            data = {'email': 'foo@example.com'}
            form = self.form_cls()(MultiDict(data))
            assert form.validate()

    def test_required(self):
        with app.test_request_context():
            form = self.form_cls()()
            assert not form.validate()
            msg = ['This field is required.']
            assert form.email.errors == msg

    def test_email_validation(self):
        with app.test_request_context():
            form = self.form_cls()(MultiDict({'email': 'foo.bar.com'}))
            assert not form.validate()
            assert form.email.errors == ['Invalid email address.']

    def test_custom_validation(self):
        with app.test_request_context():
            def invalid(*args, **kwargs):
                raise validators.ValidationError('Not Valid')

            form = self.form_cls(invalid)(MultiDict({'email': 'foo@bar.com'}))
            assert not form.validate()
            assert form.email.errors == ['Not Valid']


class TestLoginForm(object):
    def form_cls(self, password_validator=None, id_field=None):
        return make_login_form(
            password_validator or (lambda *args, **kwargs: None),
            id_field or make_email_login_field(lambda *args, **kwargs: None)
        )

    def test_ok(self):
        with app.test_request_context():
            data = {
                'id': 'foo@example.com',
                'password': '12345'
            }
            form = self.form_cls()(MultiDict(data))
            assert form.validate()

    def test_required(self):
        with app.test_request_context():
            form = self.form_cls()()
            assert not form.validate()
            msg = ['This field is required.']
            assert form.id.errors == msg
            assert form.password.errors == msg

    def test_custom_validation(self):
        with app.test_request_context():
            def invalid(*args, **kwargs):
                raise validators.ValidationError('Not Valid')

            form = self.form_cls(invalid)(MultiDict({'id': 'foo@bar.com', 'password': 'Foo'}))
            assert not form.validate()
            assert form.form_errors == ['Not Valid']

    def test_id_field(self):
        with app.test_request_context():
            id = fields.IntegerField('User', validators=[validators.NumberRange(min=10)])
            form = self.form_cls(id_field=id)(MultiDict({'id': '3', 'password': 'Foo'}))
            assert not form.validate()
            assert form.id.errors == ['Number must be at least 10.']

            form = self.form_cls(id_field=id)(MultiDict({'id': '15', 'password': 'Foo'}))
            assert form.validate()

    def test_remember_me_enabled(self):
        with app.test_request_context():
            data = {
                'id': 'foo@example.com',
                'password': '12345',
            }
            form = self.form_cls()(MultiDict(data))
            assert form.remember_me.data is False

            data['remember_me'] = True
            form = self.form_cls()(MultiDict(data))
            assert form.remember_me.data is True

    def test_remember_me_disabled(self):
        form_cls = make_login_form(
            lambda *args, **kwargs: None,
            make_email_login_field(lambda *args, **kwargs: None),
            enable_remember_me=False
        )
        with app.test_request_context():
            data = {
                'id': 'foo@example.com',
                'password': '12345',
                'remember_me': True
            }
            form = form_cls(MultiDict(data))
            assert not hasattr(form, 'remember_me')
            assert form.validate()
            assert 'remember_me' not in form.data


class TestResetPasswordForm(object):
    def form_cls(self, pw_validators=None):
        return make_reset_password_form(pw_validators)

    def test_ok(self):
        with app.test_request_context():
            data = {
                'new_password': 'password',
                'retype_password': 'password'
            }
            form = self.form_cls()(MultiDict(data))
            assert form.validate()

    def test_required(self):
        with app.test_request_context():
            form = self.form_cls()()
            assert not form.validate()
            msg = ['This field is required.']
            assert form.new_password.errors == msg
            assert form.retype_password.errors == []

    def test_retype_validation(self):
        with app.test_request_context():
            data = {
                'new_password': 'password',
                'retype_password': 'passw0rd'
            }
            form = self.form_cls()(MultiDict(data))
            assert not form.validate()
            assert form.new_password.errors == []
            assert form.retype_password.errors == ['Passwords do not match']


class TestBoolValidator(object):
    def form_inst(self, pw_validators=None):
        return make_reset_password_form(pw_validators)(MultiDict({
                'new_password': 'password',
                'retype_password': 'password'
            }))

    def test_ok(self):
        with app.test_request_context():
            form = self.form_inst([bool_validator(lambda x: True, 'Invalid')])
            assert form.validate()

    def test_invalid(self):
        with app.test_request_context():
            form = self.form_inst([bool_validator(lambda x: False, 'Invalid')])
            assert not form.validate()
            assert form.new_password.errors == ['Invalid']
