from flask import jsonify

from flask_atomic.http.exceptions import HTTPException

from . import error_handler

ERRMAP = {
    404: 'Cannot process this request as this resource does not exist',
    400: 'Bad request. Cannot process request. Check inputs and resource IDs',
    429: 'Too many requests. Please try again later.',
    500: 'Server has encountered an issue. Please reach out to support is issue persists',
    401: 'Unauthorised access for this resource',
    403: 'Resource(s) is forbidden',
    409: 'Ooops, seems this entry has already been added!'
}


@error_handler.app_errorhandler(HTTPException)
@error_handler.app_errorhandler(Exception)
def catch_error(error=0):
    """
    Catch service wide errors here. Should expand this out more. TODO

    Currently, anything not 404, will reroute to 500 error page. Not
    explicitly defined there as such that it is a 500, as this isn't
    useful for general users.

    TODO: report when 500 failures occur to some mail for maximum awesome service management

    :param HTTPException error:
    :return: error page template
    :rtype: str
    """

    if isinstance(error, HTTPException):
        return error.pack()

    if getattr(error, 'code', None):
        return jsonify(error=str(error)), error.code
    return jsonify(error=ERRMAP[500], message=str(error))
