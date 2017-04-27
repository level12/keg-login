import keg_login.middleware as middleware


class TestLockedOutMiddleware(object):
    def test_excluded_routes(self):
        cls = middleware.LockedOutMiddleware
        # No Session Key
        assert not cls().should_lock_out('thing', {})

        # In default excluded
        assert not cls().should_lock_out('static', {'keg-login.lockout': True})

        # In extra routes
        assert not cls(exclude={'thingy'}).should_lock_out('thingy', {'keg-login.lockout': True})

        # Sad path
        assert cls().should_lock_out('thingy', {'keg-login.lockout': True})
