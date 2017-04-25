from datetime import date
import binascii

import flask
from keg_elements.crypto import (
    constant_time_compare,
    salted_hmac,
)
from keg_elements.http import (
    base36_to_int,
    int_to_base36,
)
from keg_elements.encoding import force_bytes


class PasswordResetTokenGenerator:
    """Generate secure password reset tokens

    This code was largely borrowed from Django and adapted for use in the Keg
    ecosystem.
    """

    key_salt = "keg_login.libs.tokens.PasswordResetTokenGenerator"

    @property
    def timeout_days(self):
        """Number of days before the reset token will timeout"""
        return flask.current_app.config.get('PASSWORD_RESET_TIMEOUT_DAYS', 1)

    @property
    def _secret(self):
        return flask.current_app.config['PASSWORD_RESET_SECRET']

    def make_token(self, user):
        """Return a token that can be used once to do a password reset for the given user."""
        return self._make_token_with_timestamp(user, self._num_days(self._today()))

    def check_token(self, user, token):
        """Check that a password reset token is correct for a given user."""
        if not (user and token):
            return False

        # Parse the token
        try:
            ts_b36, hash = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with in a way that
        # isn't seceptiable to timing attacks
        if not constant_time_compare(
            # Regenerate the toke with the user and the timestamp when we
            # created the token in the first place. This should generate an
            # identitcal token from when we created it last time. If anything
            # changed in the _make_hash_function, this will fail.
            force_bytes(self._make_token_with_timestamp(user, ts)),

            # Compare that against the token we received from the URL which, if
            # untampered is what was sent to the user.
            force_bytes(token)
        ):
            return False

        # Check the timestamp is within limit
        if (self._num_days(self._today()) - ts) >= self.timeout_days:
            return False

        return True

    def _make_token_with_timestamp(self, user, timestamp):
        # timestamp is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        ts_b36 = int_to_base36(timestamp)

        # By hashing on the internal state of the user and using state that is sure to change we
        # produce a hash that will be invalid as soon as it is used.
        hash = salted_hmac(
            self.key_salt,
            self._make_hash_value(user, timestamp),
            self._secret
        )

        # This generates a really long hex value  based on the hash from the
        # HMAC... we really don't need all of it, so we trim it down to keep the
        # url shorter.
        prepared_hash = binascii.hexlify(hash).decode()[::2]

        return "%s-%s" % (ts_b36, prepared_hash)

    def _last_login(self, user):
        """Return a timestamp of the last time a user logged in"""
        return user.last_login

    def _make_hash_value(self, user, timestamp):
        last_login = self._last_login(user)

        login_timestamp = ('' if last_login is None
                           else last_login.replace(microsecond=0, tzinfo=None))

        return str(user.id) + str(user.password) + str(login_timestamp) + str(timestamp)

    def _num_days(self, dt):
        return (dt - date(2001, 1, 1)).days

    def _today(self):
        # Used for mocking in tests
        return date.today()
