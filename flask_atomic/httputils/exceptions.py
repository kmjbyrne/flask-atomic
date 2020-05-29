class HTTPException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class HTTPAbstractException(Exception):
    pass


class HTTPConflict(HTTPAbstractException):
    code = 409

    def __init__(self, message):
        self.message = message