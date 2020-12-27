from functools import wraps

from flask import jsonify
from flask import current_app

from flask_atomic.auth.jwt import confirm_token


def check_request_token(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if not current_app.config.get('SECURED', True):
            return func(*args, **kwargs)
        auth_token = confirm_token()
        if type(auth_token) == str:
            return jsonify(message='Token is invalid', code=403), 403
        # g.user = auth_token.get('user')
        return func(*args, **kwargs)
    return decorated

