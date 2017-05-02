from __future__ import absolute_import

import flask
import flask_login
import keg.web
import wrapt
from wtforms.validators import ValidationError

from . import forms
from .lib import (
    Flash,
    LoggedInResponder,
    RedirectResponse,
    Responder,
)

__all__ = [
    'ChangePassword',
    'ForgotPassword',
    'Login',
    'Logout',
    'ResetPassword',
]


def requires_login(current_user=flask_login.current_user):
    @wrapt.decorator
    def decorator(fn, instance, args, kwargs):
        return (fn(*args, **kwargs) if current_user and current_user.is_authenticated
                else flask.abort(401))

    return decorator


def to_wtforms_validator(validator):
    def wtforms_validator(form, field):
        return validator(field.data)
    return wtforms_validator


class KegLoginView(keg.web.BaseView):
    url = None

    class Responder(Responder):
        pass

    def get_responder(self):
        return self.Responder(
            query_args=flask.request.args,
            default_template_args=self.base_template_args()
        )


class CanSetLock(object):
    def set_lockout(self):
        flask.session['keg-login.lockout'] = True


class CanRemoveLock(object):
    def remove_lockout(self):
        flask.session.pop('keg-login.lockout', None)


class CanLogin(object):
    """Mixin to capture the login effect. Defaults to Flask-Login's behavior."""
    def login_user(self, user, remember, *args, **kwargs):
        return flask_login.login_user(user, remember, *args, **kwargs)  # pragma: no cover


class CanLogout(object):
    """Mixin to capture the logout effect. Defaults to Flask-Login's behavior."""
    def logout_user(self):
        flask_login.logout_user()  # pragma: no cover


class NeedsCurrentUser(object):
    """Mixin to capture the effect of looking at the current user."""
    def get_current_user(self):
        return flask_login.current_user  # pragma: no cover


class ChangePassword(KegLoginView, NeedsCurrentUser):
    url = '/change-password'

    class Responder(LoggedInResponder):
        template = 'keg-login/change-password.html'

        def verify_old_password(self, password):
            return self.user.verify_password(password)

        def new_password_validators(self):
            pass  # pragma: no cover

        def make_form(self):
            _validate_old_password = forms.bool_validator(
                lambda data: self.verify_old_password(data),
                u'Old password is not correct'
            )

            form_cls = forms.make_change_password_form(
                [_validate_old_password],
                list(map(to_wtforms_validator, self.new_password_validators()))
            )
            return form_cls(next=self.get_next_url(), **(self.form_kwargs or {}))

        def update_password(self, user, password):
            user.set_password(password)

        def handle_successful_reset(self):
            """Returns a list of `Flash` messages."""
            return [Flash(u'Your password has been changed successfully.', 'success')]

        def get(self):
            return self.render_with({'form': self.make_form()})

        def post(self):
            form = self.make_form()

            if form.validate():
                self.update_password(self.user, form.new_password.data)
                flashes = self.handle_successful_reset()
                return RedirectResponse(form.next.data, flashes)

            return self.render_with({'form': form})

    def get_responder(self):
        current_user = self.get_current_user()
        return requires_login(current_user)(
            lambda: self.Responder(
                user=current_user,
                query_args=flask.request.args,
                default_template_args=self.base_template_args()
            )
        )()

    def get(self):
        return self.get_responder().get().as_flask_response()

    def post(self):
        return self.get_responder().post().as_flask_response()


class ForgotPassword(KegLoginView):
    url = '/forgot-password'

    class Responder(Responder):
        template = 'keg-login/forgot-password.html'

        def make_form(self):
            form_cls = forms.make_forgot_password_form()
            return form_cls(next=self.get_next_url(), **(self.form_kwargs or {}))

        def request_password_reset(self, email):
            """Do actions necessary to request a new password for the given email.

            :returns: `Flash` messages.
            """
            raise NotImplementedError()  # pragma: no cover

        def get(self):
            return self.render_with({'form': self.make_form()})

        def post(self):
            form = self.make_form()

            if form.validate():
                flashes = self.request_password_reset(form.email.data)
                return RedirectResponse(form.next.data, flashes)

            return self.render_with({'form': form})

    def get(self):
        return self.get_responder().get().as_flask_response()

    def post(self):
        return self.get_responder().post().as_flask_response()


class Lock(KegLoginView, NeedsCurrentUser):
    url = '/lock'

    class Responder(LoggedInResponder, CanSetLock, CanRemoveLock):
        template = 'keg-login/lock.html'

        def make_form(self):
            formcls = forms.make_lock_form()
            return formcls(next=self.get_next_url(), **(self.form_kwargs or {}))

        def get(self):
            self.set_lockout()
            return self.render_with({
                'form': self.make_form(),
                'user': self.user,
            })

        def post(self):
            form = self.make_form()

            if not form.validate():
                return self.render_with(
                    {'form': form},
                    [Flash(u'The submission was invalid', 'error')]
                )

            if not self.user.verify_password(form.password.data):
                return self.render_with(
                    {'form': form},
                    [Flash(u'That is not the correct password.', 'error')]
                )

            self.remove_lockout()
            return RedirectResponse(form.data['next'], [])

    def get_responder(self):
        return self.Responder(user=self.get_current_user(), query_args=flask.request.args)

    def get(self):
        return self.get_responder().get().as_flask_response()

    def post(self):
        return self.get_responder().post().as_flask_response()


class Login(KegLoginView):
    url = '/login'

    class Responder(Responder, CanLogin):
        template = 'keg-login/login.html'
        enable_remember_me = True

        def get_id_form_field(self, user_password_validator=None):
            """Returns a WTForms field object to represent the ID of a user. For example, this might be
            a username, an email, or both. The field should validate its input."""
            return forms.make_email_login_field(user_password_validator)

        def get_user_by_id(self, id):
            """Returns a user entity based on the id field from the login form or None if no match was
            found."""
            raise NotImplementedError()  # pragma: no cover

        def verify_password(self, user, password):
            return user.verify_password(password)

        def make_form(self):
            def validate_password(form):
                user = self.get_user_by_id(form.id.data)
                if not user or not self.verify_password(user, form.password.data):
                    raise ValidationError(u'Invalid user or password')

            form_cls = forms.make_login_form(
                validate_password,
                self.get_id_form_field(),
                enable_remember_me=self.enable_remember_me
            )
            return form_cls(next=self.get_next_url(), **(self.form_kwargs or {}))

        def check_user_blocked_from_login_attempt(self, user):
            """Returns `Flash` messages IFF the given user is not even permitted to attempt a login.
            This check happens if a user can be found for the given identity."""
            return []  # pragma: no cover

        def check_user_blocked_from_login(self, user):
            """Returns `Flash` messages IFF the given user is blocked from logging in even after
            providing proper credentials."""
            return []  # pragma: no cover

        def handle_login_success(self, user):
            """Does some stuff when a user enters the proper credentials and is not blocked from
            login.

            :returns: `Flash` messages.
            """
            return [Flash('Welcome!', 'success')]  # pragma: no cover

        def handle_login_failure(self, user):
            """Does some stuff when a valid user enters a wrong password. E.g. log messages, etc."""
            pass  # pragma: no cover

        def get_current_user(self):
            return flask_login.current_user  # pragma: no cover

        def get(self):
            return self.render_with({'form': self.make_form()})

        def post(self):
            form = self.make_form()
            user = self.get_user_by_id(form.id.data)

            attempt_blocked_flashes = (self.check_user_blocked_from_login_attempt(user)
                                       if user else [])
            if attempt_blocked_flashes:
                return self.render_with({'form': form}, attempt_blocked_flashes)

            if form.validate():
                login_blocked_flashes = self.check_user_blocked_from_login(user)
                if login_blocked_flashes:
                    return self.render_with({'form': form}, login_blocked_flashes)

                flashes = self.handle_login_success(user)
                self.login_user(user, remember=self.enable_remember_me and form.remember_me.data)
                return RedirectResponse(form.next.data, flashes)

            if user:
                self.handle_login_failure(user)

            return self.render_with({'form': form}, ())

    def get(self):
        responder = self.get_responder()
        current_user = responder.get_current_user()
        return (
            RedirectResponse(responder.get_next_url(), [])  # Skip login form when logged in.
            if current_user and current_user.is_authenticated
            else responder.get()
        ).as_flask_response()

    def post(self):
        return self.get_responder().post().as_flask_response()


class Logout(KegLoginView, NeedsCurrentUser):
    url = '/logout'

    class Responder(LoggedInResponder, CanLogout):
        def get(self):
            self.logout_user()
            return RedirectResponse(
                self.get_next_url(),
                [Flash(u'You have logged out successfully.', 'success')]
            )

    def get_responder(self):
        return self.Responder(user=self.get_current_user(), query_args=flask.request.args)

    def get(self):
        return self.get_responder().get().as_flask_response()


class ResetPassword(KegLoginView, NeedsCurrentUser, CanLogout):
    url = '/reset-password/<token>'

    class Responder(Responder):
        template = 'keg-login/reset-password.html'

        def __init__(self, token, *args, **kwargs):
            self.token = token
            super(ResetPassword.Responder, self).__init__(*args, **kwargs)

        class InvalidResetTokenError(Exception):
            default_error_message = u'That reset token is invalid.'

            def __init__(self, message=None):
                self.message = message or self.default_error_message
                super(ResetPassword.Responder.InvalidResetTokenError, self).__init__(
                    self.message)

        class ExpiredResetTokenError(InvalidResetTokenError):
            default_error_message = u'That reset token has expired.'

        def process_reset_token(self, reset_token):
            """Returns a user object and any additional data for the given reset token.

            :param reset_token: is the token to use for looking up a user.
            :returns: a 2-tuple like (user, token_data) where
                        * user is the user entity for the reset token or
                          None to imply `self.InvalidResetTokenError`.
                        * token_data is any other data to remember about the token.

            :raises: `self.InvalidResetTokenError`

            `InvalidResetTokenErrors` are flashed to the page for the user to see.
            """
            raise NotImplementedError()  # pragma: no cover

        def update_password(self, user, token_data, new_password):
            user.set_password(new_password)

        def handle_successful_reset(self, user, token_data, reset_token, new_password):
            """Does any action necessary to mark a reset token as being used."""
            self.update_password(user, token_data, new_password)
            return RedirectResponse(
                self.get_next_url(),
                [Flash(u'Your password has been reset successfully.', 'success')]
            )

        def new_password_validators(self, user):
            return []  # pragma: no cover

        def make_form(self, user, token_data):
            password_validators = list(
                map(to_wtforms_validator, self.new_password_validators(user))
            )
            form_cls = forms.make_reset_password_form(password_validators)
            return form_cls(next=self.get_next_url(), **(self.form_kwargs or {}))

        def respond(self, is_post):
            user = None
            try:
                user, token_data = self.process_reset_token(self.token)
                if not user:
                    raise self.InvalidResetTokenError()
            except self.InvalidResetTokenError as e:
                return RedirectResponse(self.get_next_url(), [Flash(e.message, 'error')])

            form = self.make_form(user, token_data)

            if is_post and form.validate():
                return self.handle_successful_reset(
                    user,
                    token_data,
                    self.token,
                    form.new_password.data
                )

            return self.render_with({'form': form})

        def get(self):
            return self.respond(False)

        def post(self):
            return self.respond(True)

    def get_responder(self, token):
        return self.Responder(
            token=token,
            query_args=flask.request.args,
            default_template_args=self.base_template_args()
        )

    def get(self, token):
        current_user = self.get_current_user()
        if current_user and current_user.is_authenticated:
            self.logout_user()
        return self.get_responder(token).get().as_flask_response()

    def post(self, token):
        return self.get_responder(token).post().as_flask_response()
