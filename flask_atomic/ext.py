from datetime import datetime

from flask import Flask
from flask import Response
from flask import jsonify
from flask.json import JSONEncoder

from sqlalchemy.orm.collections import InstrumentedList

from sqlalchemy_blender import serialize
from sqlalchemy_blender import iserialize
from handyhttp import HTTPException


class ModelEncoder(JSONEncoder):
    def default(self, data):
        if isinstance(data, HTTPException):
            return data.pack()
        if isinstance(data, InstrumentedList):
            return serialize(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            data = iserialize(data)
        return data


class JSONResponse(Response):
    @classmethod
    def force_type(cls, rv, environ=None):
        if isinstance(rv, HTTPException):
            return rv.pack()
        if isinstance(rv, dict):
            rv = jsonify(rv)
        elif isinstance(rv, tuple):
            rv = jsonify(rv[0]), rv[1]
        return super(JSONResponse, cls).force_type(rv, environ)


class FlaskJSON(Flask):
    response_class = JSONResponse
    json_encoder = ModelEncoder
