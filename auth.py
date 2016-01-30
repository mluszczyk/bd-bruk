"""Well, it was required and the easiest way (as we can't use ORM).
"""
import functools

from flask import request, redirect
import werkzeug.exceptions


SECRET_PASSWORD = 'swinkitrzy'


def login_required(app):
    def decorator(f):
        def caller(*args, **kwargs):
            if request.cookies.get('password') != SECRET_PASSWORD:
                raise werkzeug.exceptions.Forbidden
            else:
                return f(*args, **kwargs)
        return functools.update_wrapper(caller, f)
    return decorator


def login_factory(app):
    def login():
        if request.args.get('password') != SECRET_PASSWORD:
            raise werkzeug.exceptions.Forbidden
        else:
            redir = redirect("/")
            response = app.make_response(redir)
            response.set_cookie('password', value=SECRET_PASSWORD)
            return response
    return login
