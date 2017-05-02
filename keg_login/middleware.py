import flask


class LockedOutMiddleware(object):
    lock_endpoint = 'keg_login.lock'

    session_key_name = 'keg-login.lockout'

    default_excluded_routes = frozenset([
        'static',
        'keg_login.logout',
        lock_endpoint,
    ])

    def __init__(self, exclude=frozenset()):
        self.exclude_routes = exclude | self.default_excluded_routes

    def should_lock_out(self, endpoint, session):
        if not session.get(self.session_key_name, False):
            return False

        return False if endpoint in self.exclude_routes else True

    def __call__(self):
        if self.should_lock_out(flask.request.endpoint, flask.session):
            return flask.redirect(flask.url_for(self.lock_endpoint))
