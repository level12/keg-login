from pathlib import Path

from blazeutils import randchars
import flask
from wtforms import validators

from keg_login import views
from keg_login.lib import TemplateResponse, RedirectResponse, Flash

template_dir = str(Path(__file__).parent.parent / 'templates')

bp = flask.Blueprint('keg_login', __name__, template_folder=template_dir)
app = flask.Flask(__name__, template_folder=template_dir)

app.config['WTF_CSRF_ENABLED'] = False
app.secret_key = randchars()


class User(object):
    def __init__(self, email, password, is_active=True, is_authenticated=False):
        self.email = email
        self.password = password
        self.is_active = is_active
        self.is_authenticated = is_authenticated

    def verify_password(self, pw):
        return pw == self.password

    def set_password(self, pw):
        self.password = pw


class ResponderTestBase(object):
    def make_user(self, email=None, password=None):
        return User(email or randchars(), password or randchars())


class TestChangePasswordResponder(ResponderTestBase):
    class Responder(views.ChangePassword.Responder):
        default_next_endpoint = ''

        def new_password_validators(self):
            return []

        def get_next_url(self):
            return '/'

    def test_change_password_invalid_old_password(self):
        user = self.make_user(password=None)
        user.set_password('A-password')

        with app.test_request_context():
            responder = self.Responder(user, form_kwargs={
                'old_password': u'B-password',
                'new_password': u'C-password',
                'retype_password': u'C-password',
            })

            response = responder.post()

        assert type(response) == TemplateResponse
        assert response.template_args['form'].old_password.errors == ['Old password is not correct']
        assert response.flash_messages == ()
        assert user.verify_password('A-password')

    def test_change_password_successful(self):
        user = self.make_user(password=None)
        user.set_password('A-password')

        with app.test_request_context():
            responder = self.Responder(user, form_kwargs={
                'old_password': u'A-password',
                'new_password': u'B-password',
                'retype_password': u'B-password',
            })

            response = responder.post()

        assert type(response) == RedirectResponse
        assert response.flash_messages == [
            Flash('Your password has been changed successfully.', 'success')]
        assert response.url == '/'
        assert user.verify_password('B-password')

    def test_get(self):
        with app.test_request_context():
            responder = self.Responder(None)
            response = responder.get()
        assert type(response) == TemplateResponse
        assert response.template_args['form']


current_user = None


class TestChangePasswordView(object):
    class ChangePassword(views.ChangePassword):
        blueprint = bp

        def get_current_user(self):
            return current_user

        def base_template_args(self):
            return {}

        class Responder(views.ChangePassword.Responder):
            def get_next_url(self):
                return '/'

            def new_password_validators(self):
                return []

    """Tests including full request cycle and all effects."""

    def test_change_password_view_requires_being_logged_in(self):
        global current_user
        current_user = User('user@example.com', 'passW0rd')
        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.get('/change-password')
        assert response.status_code == 401

        response = test_app.post('/change-password')
        assert response.status_code == 401

    def test_change_password_view_get(self):
        global current_user
        current_user = User('user@example.com', 'passW0rd', is_authenticated=True)
        test_app = app.test_client()
        response = test_app.get('/change-password')
        assert response.status_code == 200

    def test_change_password_view_post(self):
        global current_user
        current_user = User('user@example.com', 'passW0rd', is_authenticated=True)
        test_app = app.test_client()
        response = test_app.post('/change-password', data={
            'old_password': 'passW0rd',
            'new_password': 'new-pass1',
            'retype_password': 'new-pass1'
        })
        assert response.status_code == 302
        assert current_user.password == 'new-pass1'


class TestForgotPasswordResponder(ResponderTestBase):
    """Tests isolating [most] dependencies and effects."""

    class Responder(views.ForgotPassword.Responder):
        def __init__(self, *args, **kwargs):
            self.resets_requested = []
            super().__init__(*args, **kwargs)

        def get_next_url(self):
            return '/'

        def request_password_reset(self, email):
            self.resets_requested.append(email)
            return [Flash('Reset requested', 'success')]

    def test_forgot_password_get(self):
        with app.test_request_context():
            response = self.Responder().get()
        assert type(response) == TemplateResponse
        assert response.template_args['form']

    def test_forgot_password_invalid_email(self):
        with app.test_request_context():
            responder = self.Responder(form_kwargs={'email': 'blah'})
            response = responder.post()
        assert type(response) == TemplateResponse
        assert response.template_args['form'].email.errors == ['Invalid email address.']

    def test_forgot_password_success(self):
        with app.test_request_context():
            responder = self.Responder(None, form_kwargs={'email': 'foo@bar.com'})
            response = responder.post()

        assert type(response) == RedirectResponse
        assert response.url == '/'
        assert response.flash_messages == [Flash('Reset requested', 'success')]
        assert responder.resets_requested == ['foo@bar.com']


class TestForgotPasswordView(object):
    class ForgotPassword(views.ForgotPassword):
        blueprint = bp

        def base_template_args(self):
            return {}

        class Responder(views.ForgotPassword.Responder):
            def get_next_url(self):
                return '/'

            def request_password_reset(self, email):
                return [Flash('', 'success')]

    def setup_method(self, _):
        global current_user
        current_user = None

    """Tests including full request cycle and all effects."""

    def test_forgot_password_view_does_not_require_being_logged_in(self):
        global current_user
        current_user = User('user@example.com', 'passW0rd')
        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.get('/forgot-password')
        assert response.status_code == 200

        response = test_app.post('/forgot-password', data={})
        assert response.status_code == 200

    def test_forgot_password_view_get(self):
        test_app = app.test_client()
        response = test_app.get('/forgot-password')
        assert response.status_code == 200

    def test_forgot_password_view_post(self):
        global current_user
        current_user = User('user@example.com', 'passW0rd', is_authenticated=True)
        test_app = app.test_client()
        response = test_app.post('/forgot-password', data={'email': 'foo@bar.com'})
        assert response.status_code == 302


user_map = {}


class TestLoginResponder(ResponderTestBase):
    def make_user(self, email=None, password=None, is_active=True):
        email = email or '{}@{}.com'.format(randchars(), randchars())
        user = User(email, password or randchars(), is_active)
        user_map[user.email] = user
        return user

    class Responder(views.Login.Responder):
        def __init__(self, *args, **kwargs):
            self.login_effects = []
            super().__init__(*args, **kwargs)

        def get_user_by_id(self, id):
            return user_map.get(id)

        def login_user(self, user, remember, *args, **kwargs):
            self.login_effects.append(user)

        def get_next_url(self):
            return '/'

        def check_user_blocked_from_login_attempt(self, user):
            if user.email == 'blocked_user@example.com':
                return [Flash('Blocked User', 'error')]
            return []

        def check_user_blocked_from_login(self, user):
            if not user.is_active:
                return [Flash('Inactive User', 'error')]
            return []

    def assert_login_failure(self, user, message):
        with app.test_request_context():
            responder = self.Responder(form_kwargs={
                'id': user.email,
                'password': user.password
            })
            response = responder.post()

        assert type(response) == TemplateResponse
        assert response.flash_messages == [Flash(message, 'error')]
        assert responder.login_effects == []

    def test_login_get(self):
        with app.test_request_context():
            response = self.Responder().get()
        assert type(response) == TemplateResponse
        assert response.template_args['form']

    def test_login_blocked_user(self):
        self.assert_login_failure(
            self.make_user(email='blocked_user@example.com', password='123'),
            'Blocked User'
        )

    def test_login_inactive(self):
        self.assert_login_failure(
            self.make_user(is_active=False),
            'Inactive User'
        )

    def test_login_bad_password(self):
        user = self.make_user()
        with app.test_request_context():
            responder = self.Responder(form_kwargs={
                'id': user.email,
                'password': 'bad-password'
            })

            response = responder.post()

        assert type(response) == TemplateResponse
        assert not response.flash_messages
        assert responder.login_effects == []

    def test_login_success(self):
        with app.test_request_context():
            user = self.make_user(email='user@example.com', password='password123')
            responder = self.Responder(form_kwargs={
                'id': user.email,
                'password': user.password
            })

            response = responder.post()
        assert type(response) == RedirectResponse
        assert response.url == '/'
        assert response.flash_messages == [Flash('Welcome!', 'success')]
        assert responder.login_effects == [user]


class TestLoginView(object):
    class Login(views.Login):
        blueprint = bp

        def base_template_args(self):
            return {}

        class Responder(views.Login.Responder):
            def get_next_url(self):
                return '/'

            def get_current_user(self):
                return current_user

            def login_user(self, user, remember, *args, **kwargs):
                global current_user
                current_user = user

            def get_user_by_id(self, id):
                return user_map.get(id)

    def setup_method(self, _):
        global current_user
        current_user = None

    """Tests including full request cycle and all effects."""

    def test_login_view_does_not_require_being_logged_in(self):
        global current_user
        current_user = User('user@example.com', 'passW0rd')
        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.get('/login')
        assert response.status_code == 200

        response = test_app.post('/login', data={})
        assert response.status_code == 200

    def test_redirect_already_logged_in(self):
        global current_user
        current_user = User('foo@bar.com', '123', is_authenticated=True)
        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.get('/login')
        assert response.status_code == 302
        assert response.location == 'http://localhost/'

    def test_login_view_get(self):
        test_app = app.test_client()
        response = test_app.get('/login')
        assert response.status_code == 200

    def test_login_view_post(self):
        user = User('foo@bar.com', 'passW0rd')
        user_map['foo@bar.com'] = user

        test_app = app.test_client()
        response = test_app.post('/login', data={'id': 'foo@bar.com', 'password': 'passW0rd'})
        assert response.status_code == 302
        assert current_user == user

    def test_login_view_bad_password(self):
        user = User('foo@bar.com', 'passW0rd')
        user_map['foo@bar.com'] = user

        test_app = app.test_client()
        response = test_app.post('/login', data={'id': 'foo@bar.com', 'password': 'foo'})
        assert response.status_code == 200
        assert current_user is None


class TestLogoutResponder(ResponderTestBase):
    """Tests isolating [most] dependencies and effects."""

    class Responder(views.Logout.Responder):
        def __init__(self, *a, **kw):
            self.logout_effects = 0
            super().__init__(*a, **kw)

        def logout_user(self):
            self.logout_effects += 1

        def get_next_url(self):
            return '/'

    def test_logout(self):
        user = self.make_user()
        responder = self.Responder(user)

        with app.test_request_context():
            response = responder.get()
        assert type(response) == RedirectResponse
        assert response.flash_messages == [Flash('You have logged out successfully.', 'success')]
        assert response.url == '/'
        assert responder.logout_effects == 1

        with app.test_request_context():
            response = responder.get()
        assert type(response) == RedirectResponse
        assert response.flash_messages == [Flash('You have logged out successfully.', 'success')]
        assert response.url == '/'
        assert responder.logout_effects == 2


class TestLogoutView(object):
    class Logout(views.Logout):
        blueprint = bp

        def get_current_user(self):
            return current_user

        class Responder(views.Logout.Responder):
            def get_next_url(self):
                return '/'

            def logout_user(self):
                global current_user
                current_user = None

    def setup_method(self, _):
        global current_user
        current_user = None

    """Tests including full request cycle and all effects."""

    def test_logout(self):
        global current_user
        current_user = User('foo@example.com', 'password', is_authenticated=True)
        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.get('/logout')
        assert response.status_code == 302
        assert current_user is None


token_map = {}


class TestResetPasswordResponder(ResponderTestBase):
    """Tests isolating [most] dependencies and effects."""

    class Responder(views.ResetPassword.Responder):
        def __init__(self, *a, **kw):

            super().__init__(*a, **kw)

        def process_reset_token(self, reset_token):
            return token_map.get(reset_token), reset_token

        def get_next_url(self):
            return '/'

        def new_password_validators(self, user):
            def valid(d):
                if d.endswith('123'):
                    raise validators.ValidationError('bad password')
            return [valid]

    def make_token(self, token=None, user=None):
        user = user or User('{}@{}.com'.format(randchars(), randchars()), randchars())
        token = token or randchars()
        token_map[token] = user
        return token

    def test_invalid_token(self):
        responder = self.Responder(token=b'blah')
        with app.test_request_context():
            for response in [responder.get(), responder.post()]:
                assert type(response) == RedirectResponse
                assert response.url == '/'
                assert response.flash_messages == [Flash('That reset token is invalid.', 'error')]

    def test_reset_get_successful(self):
        responder = self.Responder(token=self.make_token())
        with app.test_request_context():
            response = responder.get()
        assert type(response) == TemplateResponse
        assert response.template_args['form']

    def test_reset_password_successful(self):
        token = self.make_token()
        user = token_map[token]
        responder = self.Responder(token=token, form_kwargs={
            'new_password': 'new-pass',
            'retype_password': 'new-pass'
        })
        with app.test_request_context():
            response = responder.post()
            assert type(response) == RedirectResponse
            assert response.url == '/'
            assert response.flash_messages == [
                Flash('Your password has been reset successfully.', 'success')]
            assert user.password == 'new-pass'

    def test_reset_form_error(self):
        token = self.make_token()
        user = token_map[token]
        responder = self.Responder(token=token, form_kwargs={
            'new_password': 'new-pass',
            'retype_password': 'new-pass1'
        })
        with app.test_request_context():
            response = responder.post()
            assert type(response) == TemplateResponse
            assert not response.flash_messages
            assert user.password != 'new-pass'

    def test_validator_error(self):
        token = self.make_token()
        user = token_map[token]
        responder = self.Responder(token=token, form_kwargs={
            'new_password': 'new-pass123',
            'retype_password': 'new-pass123'
        })
        with app.test_request_context():
            response = responder.post()
            assert type(response) == TemplateResponse
            assert not response.flash_messages
            assert user.password != 'new-pass123'


class TestResetPasswordView(object):
    class ResetPassword(views.ResetPassword):
        blueprint = bp

        def base_template_args(self):
            return {}

        def get_current_user(self):
            return current_user

        def logout_user(self):
            global current_user
            current_user = None

        class Responder(views.ResetPassword.Responder):
            def get_next_url(self):
                return '/'

            def process_reset_token(self, reset_token):
                return token_map.get(reset_token), reset_token

    def setup_method(self, _):
        global current_user
        current_user = None

    """Tests including full request cycle and all effects."""

    def test_reset_password_post(self):
        user = User('foo@example.com', 'password')
        token = randchars()
        token_map[token] = user

        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.post('/reset-password/{}'.format(token), data={
            'new_password': 'abc123',
            'retype_password': 'abc123'
        })
        assert response.status_code == 302
        assert user.password == 'abc123'

    def test_reset_password_get(self):
        user = User('foo@example.com', 'password')
        token = randchars()
        token_map[token] = user

        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.get('/reset-password/{}'.format(token), )
        assert response.status_code == 200
        assert current_user is None

    def test_reset_password_get_with_logged_in_user(self):
        global current_user
        current_user = User('bar@example.com', 'drowssap', is_authenticated=True)

        user = User('foo@example.com', 'password')
        token = randchars()
        token_map[token] = user

        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.get('/reset-password/{}'.format(token), )
        assert response.status_code == 200
        assert current_user is None

    def test_reset_password_post_bad_token(self):
        app.register_blueprint(bp)

        test_app = app.test_client()
        response = test_app.post('/reset-password/{}'.format(randchars()), data={
            'new_password': 'abc123',
            'retype_password': 'abc123'
        })
        assert response.status_code == 302
