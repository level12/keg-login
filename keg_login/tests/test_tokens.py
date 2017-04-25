from datetime import datetime as dt, date as d, timedelta as td

import pytest

import keg_login.tokens as tokens


@pytest.fixture(scope="module")
def prtg():
    return MockPRTG()


@pytest.fixture(scope="module")
def user():
    return MockUser()


class MockPRTG(tokens.PasswordResetTokenGenerator):
    """Mock out the PRTG with testable values"""

    _testing_today = None
    _testing_secret = None
    _testing_timeout = None

    def setup(self, timeout=None, secret=None, today=None, salt=None):
        self._testing_timeout = timeout
        self._testing_secret = secret
        self._testing_today = today
        self.key_salt = salt or self.key_salt

    @property
    def timeout_days(self):
        return self._testing_timeout or 1

    @property
    def _secret(self):
        return self._testing_secret or 'secret'

    def _today(self):
        return self._testing_today or d(2001, 1, 1)


class MockUser(object):
    def __init__(self, id=1, last_login=dt(2001, 1, 1),
                 password='password'):
        self.id = id
        self.last_login = last_login
        self.password = password


class TestPasswordResetTokenGenerator(object):

    def test_hash_value_changes_with_different_inputs(self, prtg, user):
        ts = dt(2017, 1, 1)
        default = prtg._make_hash_value(user, ts)

        # check for purity
        assert default == prtg._make_hash_value(user, ts)

        # Check different inputs
        assert default != prtg._make_hash_value(user, dt(2001, 1, 2))
        assert default != prtg._make_hash_value(MockUser(id=0), ts)
        assert default != prtg._make_hash_value(MockUser(last_login=dt(2001, 1, 2)), ts)
        assert default != prtg._make_hash_value(MockUser(password='pass'), ts)
        assert default != prtg._make_hash_value(MockUser(last_login=None), ts)

    def test_make_token_prepends_base36_ts_value(self, prtg, user):
        ts = dt(2017, 1, 1)

        ts, token1 = prtg._make_token_with_timestamp(user, 1).split('-')
        assert ts == '1'

        ts, token2 = prtg._make_token_with_timestamp(user, 100).split('-')
        assert ts == '2s'

        assert token1 != token2

    def test_make_token_unique_token(self, prtg, user):
        default = prtg._make_token_with_timestamp(user, 1)

        # Generation on different day should be the same token
        prtg.setup(today=dt(2017, 1, 2))
        assert default == prtg._make_token_with_timestamp(user, 1)

        # Different timestamp should be different token
        assert default != prtg._make_token_with_timestamp(user, 2)

        # different user should be a different token
        assert default != prtg._make_token_with_timestamp(MockUser(id=2), 1)

        # different salt should be a different token
        prtg.setup(salt='salt')
        assert default != prtg._make_token_with_timestamp(user, 1)

        # different secret should be a different token
        prtg.setup(secret='other')
        assert default != prtg._make_token_with_timestamp(user, 1)

    def test_check_token(self, user):
        prtg = MockPRTG()
        default = prtg._make_token_with_timestamp(user, 1)

        assert prtg.check_token(user, default)
        assert not prtg.check_token(user, 'bad')
        assert not prtg.check_token(MockUser(id=2), default)
        assert not prtg.check_token(None, default)
        assert not prtg.check_token(user, None)
        assert not prtg.check_token(None, None)
        assert not prtg.check_token(user, 'a-b')

        # Bad base36
        assert not prtg.check_token(user, 'zzzzzzzzzzzzzz-as')

        # Test token expiration
        prtg.setup(today=d(2001, 1, 2))  # Same day use case
        assert prtg.check_token(user, default)

        prtg.setup(today=d(2001, 1, 2) + td(hours=23, minutes=59, seconds=59))  # next day use case
        assert prtg.check_token(user, default)

        prtg.setup(today=d(2001, 1, 3))  # 24hrs +1sec
        assert not prtg.check_token(user, default)
