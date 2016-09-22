"""A small library for providing a pure interface to Flask response building."""

from collections import namedtuple

import flask


class Response(object):
    """A pure representation of all things that go into a request."""

    def as_flask_response(self):
        """Returns a Flask response including flash messages.

        Note that flash messages involve impure effects and cannot be easily rolled back.
        """
        raise NotImplementedError()  # pragma: no cover


class TemplateResponse(
    Response,
    namedtuple('TemplateResponse', 'template template_args flash_messages')
):
    """A response based on a template."""

    def render_flask_template(self):
        return flask.render_template(self.template, **self.template_args)

    def as_flask_response(self):
        for message, category in self.flash_messages:
            flask.flash(message, category)
        return self.render_flask_template()


class Flash(namedtuple('Flash', 'message category')):
    pass


class RedirectResponse(
    Response,
    namedtuple('RedirectResponse', 'url flash_messages')
):
    """A redirect response."""

    def as_flask_response(self):
        for message, category in self.flash_messages:
            flask.flash(message, category)
        return flask.redirect(self.url)


class Responder(object):
    """Totally encapsulates inputs and logic to form a response."""
    default_next_endpoint = None
    template = None

    def __init__(self, query_args=None, form_kwargs=None, default_template_args=None):
        self.query_args = query_args or {}
        self.default_template_args = default_template_args or {}
        self.form_kwargs = form_kwargs or {}

    def get_next_url(self):
        return self.query_args.get('next', self.url_for(self.default_next_endpoint))

    def render_with(self, template_args=None, flash_messages=()):
        args = self.default_template_args.copy()
        args.update(template_args or {})

        return TemplateResponse(self.template, args, flash_messages)

    def url_for(self, *args, **kwargs):
        """Allows responder to be isolated from app configuration."""
        return flask.url_for(*args, **kwargs)  # pragma: no cover


class LoggedInResponder(Responder):
    """A `Responder` that relies on a known user."""
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(LoggedInResponder, self).__init__(*args, **kwargs)
