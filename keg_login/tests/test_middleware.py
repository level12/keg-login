import keg_login.middleware as middleware


class TestLockedOutMiddleware(object):
    def test_excluded_routes(self):
        mw_class = middleware.LockedOutMiddleware
        # No Session Key
        assert not mw_class().should_lock_out('thing', {})

        # In default excluded
        assert not mw_class().should_lock_out('static', {'keg-login.lockout': True})

        # In extra routes
        assert not mw_class(exclude={'thingy'}).should_lock_out(
            'thingy', {'keg-login.lockout': True})

        # Sad path
        assert mw_class().should_lock_out('thingy', {'keg-login.lockout': True})
