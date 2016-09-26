import jinja2


__all__ = [
    'KegLogin'
]


class KegLogin(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        loader = jinja2.ChoiceLoader([
            app.jinja_loader,
            jinja2.PackageLoader('keg_login', 'templates')
        ])
        app.jinja_loader = loader
