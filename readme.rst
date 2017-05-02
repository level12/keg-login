.. default-role:: code
.. role:: python(code)
  :language: python

==========
KegLogin
==========

.. image:: https://circleci.com/gh/level12/keg-login.svg?style=svg
  :target: https://circleci.com/gh/level12/keg-login

.. image:: https://codecov.io/github/level12/keg-login/coverage.svg?branch=master
  :target: https://codecov.io/github/level12/keg-login?branch=master

.. _Keg: https://pypi.python.org/pypi/Keg

Base views and forms for user login and password management in Keg_ applications.

Usage
*****

There are 5 base views to allow users to login, logout and set their passwords.

* Login
* Logout
* ChangePassword
* ForgotPassword
* ResetPassword

To make use of these views in your application, subclass the appropriate view
and it's contained `Responder` class and implement the pure virtual methods.

You may override the templates used for these views by creating the
appropriately named template under `<my application>/templates/keg-login/` or
overriding `template` in your `Responder` subclass

Example
=======

.. code:: python

  from keg import Keg
  from keg_login.ext import KegLogin
  from keg_login import views

  app = Keg(__name__)
  KegLogin(app)

  class ForgotPassword(views.ForgotPassword):
      class Responder(views.ForgotPassword.Responder):
          def request_password_reset(self, email):
              generate_token_and_send_email(email)

Templates
=========

Keg-Login makes great use of a great Jinja2 feature called macros. they allows the
user of Keg-Login to override just the piece of functionality or design without
a lot of work. Here is how:

After install Keg-Login, create a ``keg-login`` folder in your application
template folder.


Use own template
----------------

In this folder create a file called `base.html`

Within `base.html` build or ``extend`` the template you want to surround the
login views. The only thing that Keg-Login expects is for `base.html` to expose
a ``block main`` somewhere in that file. For example...

.. code::

  {% extends your-master-template.html %}

  {# This block might be defined in your-master-template.html #}
  {% block content %}
    {% block main %}{% endblock %}
  {% endblock %}


Now Keg-Login will use the master template as the base for the auth views.


Override Keg-Login Form Rendering (Using the Macro System)
----------------------------------------------------------

Create the `macros.html` file in `app/templates/keg-login/macros.html`. At first
all we need to do is add ::

    {% extends "keg-login/_macros.html" %}

The `_macros.html` file defines all the base/default macros for rendering the
view templates. Everything in Keg-Login is a macro.

A common macro to override is the ``render_wrapper`` macro. ``render_wrapper``
and advanced feature of Jinja2 to allow the forms in Keg-Login to be "wrapped"
with additional HTML. For example, if you have a bunch of extra code you want to
surround the form elements with. This requires a little more explanation...


Say for example you have this `master` template...

.. code:: jinja2

  <body>
    <div class="container">
      {% block container %} {% endblock %}
    </div>
  </body>

You then extend this in `keg-login/base.html` like so...

.. code:: html

  {% extends "base.html" %}

  {% block container %}
    <div class="auth-container">
      {% block main %}
      {% endblock %}
    </div>
  {% endblock container %}

Without `render_wrapper`, that would be all the customization we could do to a
form. The ``input`` tag for, say, the login form would be at
``body>div.container>div.auth-container>form>input(s)``. What if our design
requires an html element between ``form`` and the form ``input``'s? That would
not be possible without overriding each form implementation (not acceptable, you
might as well not use Keg-Login at that point, or create something like
``render_wrapper``.

To use ``render_wrapper``, in your `macros.html` file but this...

.. code::

  {% macro render_wrapper() %}
    {# the form being rendered (login/forgot password/etc) will be rendered
        whereever this is placed #}
    {{ caller() }}
  {% endmacro %}


If you want to wrap the ``form`` element in a div...

.. code::

  {% macro render_wrapper() %}
    <div class="form-wrapper">
      {{ caller() }}
    </div>
  {% endmacro %}

Now, all of the keg-login forms will get this treatment.

Development
***********

Branches & State
================

* `master`: our "production" branch

All other branches are feature branches.

Environment
===========

Install requirements:

`$ pip install --use-wheel --no-index --find-links=requirements/wheelhouse -r requirements/dev-env.txt`
`$ pip install -e .`
