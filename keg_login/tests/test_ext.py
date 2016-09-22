from keg import Keg
from pyquery import PyQuery
from keg_login.ext import KegLogin
from flask import render_template

from keg_login.forms import make_change_password_form, make_forgot_password_form


class TestExtension(object):
    def get_app(self):
        app = Keg(__name__, template_folder='test_templates')
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SERVER_NAME'] = 'localhost'
        return app

    def test_loader_override(self):
        app = self.get_app()
        ext = KegLogin()
        ext.init_app(app)
        with app.app_context():
            form = make_forgot_password_form()()
            rendered = render_template('keg-login/forgot-password.html', form=form)
        assert rendered.strip() == 'TEST TEMPLATE'

    def test_loader_passthrough(self):
        app = self.get_app()
        ext = KegLogin()
        ext.init_app(app)

        with app.app_context():
            form = make_change_password_form([], [])()
            rendered = render_template('keg-login/change-password.html', form=form)
        assert PyQuery(rendered)('form input[type="submit"]').val() == 'Change Password'

    def test_import(self):
        app = self.get_app()
        ext = KegLogin()
        ext.init_app(app)

        with app.app_context():
            form = make_change_password_form([], [])()
            rendered = render_template('keg-login/test-include.html', form=form)
        assert PyQuery(rendered)('form input[type="submit"]').val() == 'Change Password'

    def test_init_from_constructor(self):
        app = self.get_app()
        KegLogin(app)

        with app.app_context():
            form = make_forgot_password_form()()
            rendered = render_template('keg-login/forgot-password.html', form=form)
        assert rendered.strip() == 'TEST TEMPLATE'
