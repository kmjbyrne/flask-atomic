
class BaseHTTPResponse:
    message: str = ''
    code: int

    def __new__(cls, *args, **kwargs):
        message = kwargs.get('message', None) or cls.message or ''
        if kwargs.get('pack', False):
            return cls
        if len(args):
            return dict(data=args[0], message=message, **kwargs), cls.code
        return dict(message=message, **kwargs), cls.code


class HTTPSuccess(BaseHTTPResponse):
    message = 'Successful request'
    code = 200


class HTTPCreated(BaseHTTPResponse):
    message = 'Resource successfully created.'
    code = 201


class HTTPUpdated(BaseHTTPResponse):
    message = 'Resource successfully updated.'
    code = 202


class HTTPDeleted(BaseHTTPResponse):
    message = 'Resource successfully marked for deletion.'
    code = 204
