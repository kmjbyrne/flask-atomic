from flask import jsonify


class HTTPException(Exception):
    message: str
    code: int

    def pack(self):
        return jsonify(error=self.message), self.code


class HTTPClientError(HTTPException):
    pass


class HTTPNotFound(HTTPException):
    code = 404
    message = 'Resource does not exist'


class HTTPConflict(HTTPException):
    code = 409
    message = 'A resource with this ID already exists'


class HTTPBadRequest(HTTPException):
    code = 400
    message = 'This request can not be fulfilled.'
