import functools
import json

from flask import Response

from flask_electron.db.flaskalchemy.database import DeclarativeBase


def checktype(data):
    response = dict()
    if isinstance(data, list):
        response = [i.extract_data([]) for i in data]
    elif isinstance(data, str):
        response = data
    elif isinstance(data, DeclarativeBase):
        response = data.extract_data()
    return response


def json_response(content, *args, **kwargs):
    content = checktype(content)
    return Response(
        json.dumps(content),
        content_type="application/json",
        *args, **kwargs
    )


JsonOKResponse = functools.partial(json_response, status=200), 200
JsonCreatedResponse = functools.partial(json_response, status=201), 201
JsonBadRequestResponse = functools.partial(json_response, status=400), 400
JsonNotAllowedResponse = functools.partial(json_response, status=405), 405
JsonOverloadResponse = functools.partial(json_response, status=429), 429
