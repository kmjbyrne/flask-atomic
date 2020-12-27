import base64
from datetime import datetime
from datetime import timedelta

import jwt

from flask import current_app
from flask import request


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


def decode_auth_token(auth_token, secret_key=None):
    if not secret_key and not current_app.config.get('SECRET_KEY', None):
        raise AttributeError('Decoding requires an application SECRET_KEY')

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


def confirm_token(token=None):
    # token = base64.standard_b64decode(token).decode('utf-8')
    # return decode_auth_token(token)
    try:
        if not token:
            token = request.headers.environ.get('HTTP_API_AUTHORIZATION')
        decoded = decode_auth_token(token)
    except Exception as error:
        return None
    return decoded
