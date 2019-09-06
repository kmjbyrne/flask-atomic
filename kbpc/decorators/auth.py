import base64
from datetime import datetime
from datetime import timedelta
from functools import wraps

import jwt
from flask import g
from flask import jsonify


def encode_auth_token(user_id, secret_key, expiry=12, algorithm='HS256'):
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(hours=expiry),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            secret_key,
            algorithm=algorithm
        )
    except Exception as e:
        return e


def decode_auth_token(auth_token, secret_key):
    try:
        payload = jwt.decode(auth_token, secret_key)
        return {
            'user': payload.get('sub', None),
            'access': True
        }
    except jwt.ExpiredSignatureError:
        return 'Auth token expired. Please log in again'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again'


def confirm_token(token):
    token = base64.standard_b64decode(token).decode('utf-8')
    return decode_auth_token(token)


def check_request_token(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        auth_token = confirm_token()
        if type(auth_token) == str:
            return jsonify(message='Token is invalid', code=403), 403
        g.user = auth_token.get('user')
        return func(*args, **kwargs)

    return decorated
