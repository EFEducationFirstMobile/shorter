from functools import wraps

from flask import request
from werkzeug.datastructures import Authorization

import flask_httpauth


class MyHTTPAuth(flask_httpauth.HTTPAuth):
    pass


class HTTPBasicAuth(MyHTTPAuth, flask_httpauth.HTTPBasicAuth):
    # copied from flask_httpauth.HTTPBasicAuth except it doesn't error
    # when it can't authenticate
    def login_optional(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if auth is None and 'Authorization' in request.headers:
                # Flask/Werkzeug do not recognize any authentication types
                # other than Basic or Digest, so here we parse the header by
                # hand
                try:
                    auth_type, token = request.headers['Authorization'].split(
                        None, 1)
                    auth = Authorization(auth_type, {'token': token})
                except ValueError:
                    # The Authorization header is either empty or has no token
                    pass

            # if the auth type does not match, we act as if there is no auth
            # this is better than failing directly, as it allows the callback
            # to handle special cases, like supporting multiple auth types
            if auth is not None and auth.type.lower() != self.scheme.lower():
                auth = None

            # Flask normally handles OPTIONS requests on its own, but in the
            # case it is configured to forward those to the application, we
            # need to ignore authentication headers and let the request through
            # to avoid unwanted interactions with CORS.
            if request.method != 'OPTIONS':  # pragma: no cover
                if auth and auth.username:
                    password = self.get_password_callback(auth.username)
                else:
                    password = None
                self.authenticate(auth, password)

            return f(*args, **kwargs)
        return decorated
