from flask import jsonify


class BaseHTTPResponse:
    message: str
    code: int

    def __new__(cls, *args, **kwargs):
        if kwargs.get('pack', False):
            return cls
        if len(args):
            return jsonify(data=args[0], message=cls.message, **kwargs), cls.code
        return jsonify(message=cls.message, **kwargs), cls.code


class HTTPSuccess(BaseHTTPResponse):
    message = 'Successful request'
    code = 200


class HTTPCreated(BaseHTTPResponse):
    message = 'Resource successfully created.'
    code = 201


class HTTPUpdated(BaseHTTPResponse):
    message = 'Resource successfully updated.'
    code = 204


class HTTPDeleted(BaseHTTPResponse):
    message = 'Resource successfully marked for deletion.'
    code = 202
