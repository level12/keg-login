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

To make use of these views in your application, subclass the appropriate view and it's contained `Responder` class and implement the pure virtual methods.

You may override the templates used for these views by creating the appropriately named template under `<my application>/templates/keg-login/` or overriding `template` in your `Responder` subclass

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
