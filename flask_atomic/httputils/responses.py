import functools
import json
from typing import Union

from flask import Response

from flask_atomic.orm.base import DeclarativeBase

# HTTP Response messages
R202 = 'Resource successfully marked for deletion'

# HTTP Response errors
E404 = 'Resource not found'
E401 = 'This action is not allowed. Forbidden'


def checktype(data: Union[list, dict, DeclarativeBase]) -> Union[list, dict]:
    """
    Some data will be returned in list format, some will be model instances.
    
    Need to just make sure that any packed data is unpacked and ready to be
    converted into JSON for the response.
    
    :param data: input data
    :return: dictionary of processed data
    :rtype: dict
    """

    if isinstance(data, list) and not isinstance(data[0], dict):
        return [i.extract_data() for i in data]
    elif isinstance(data, str):
        return data
    elif isinstance(data, DeclarativeBase):
        return data.extract_data()
    return data


def json_response(content=None, *args, **kwargs):
    """
    Creates a Flask Response object with the input data (content) and sets
    the approriate HTTP headers, i.e content-type for the moment.

    :param content: provided content
    :param args: general arguments
    :param kwargs: general keyword arguments
    :return: Flask Response object
    :rtype: Response
    """

    content = checktype(content) or dict()

    if 'message' in kwargs:
        content['message'] = kwargs.get('message')
        del kwargs['message']

    if 'error' in kwargs:
        content['error'] = kwargs.get('error')
        del kwargs['error']

    return Response(
        json.dumps(content),
        content_type="application/json",
        *args, **kwargs
    )


# Using partials here, content can be provided on top of the existing
# partial keywords used.

JsonOKResponse = functools.partial(json_response, status=200)
JsonCreatedResponse = functools.partial(json_response, status=201)
JsonDeletedResp = functools.partial(json_response, status=202, message=R202)
JsonBadRequestResp = functools.partial(json_response, status=400)
JsonNotFoundResp = functools.partial(json_response, status=404, error=E404)
JsonForbiddenResp = functools.partial(json_response, status=401, error=E401)
JsonNotAllowedResponse = functools.partial(json_response, status=405)
JsonOverloadResponse = functools.partial(json_response, status=429)
JsonConflictResponse = functools.partial(json_response, status=409)
JsonUnprocessableResponse = functools.partial(json_response, status=422)
