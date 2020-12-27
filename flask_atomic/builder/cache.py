from functools import wraps


ROUTE_TABLE = {}


def link(*args, **kwargs):
    def outer(func):
        if not ROUTE_TABLE.get(func.__name__, None):
            ROUTE_TABLE[func.__name__] = []
        ROUTE_TABLE[func.__name__].append([kwargs.get('url'), kwargs.get('methods')])
        @wraps(func)
        def link_wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        return link_wrapper
    return outer
