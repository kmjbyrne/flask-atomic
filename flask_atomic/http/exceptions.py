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


class HTTPForbidden(HTTPException):
    code = 403
    message = 'You have insufficient permissions to access this resource. If you believe this is invalid, ' \
              'please contact your system admin.'


class HTTPBadRequest(HTTPException):
    code = 400
    message = 'This request can not be fulfilled.'
