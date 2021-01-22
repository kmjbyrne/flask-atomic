from flask import Flask
from flask import Blueprint


DEFAULT_METHOD_SET = ['GET', 'POST', 'PUT', 'DELETE']


def route(rule, **options):
    """
    A decorator that is used to define custom routes for methods in
    FlaskView subclasses. The format is exactly the same as Flask's
    `@app.route` decorator.
    """

    def decorator(f):
        # Put the rule cache on the method itself instead of globally
        if not hasattr(f, '_rule_cache') or f._rule_cache is None:
            f._rule_cache = {f.__name__: [(rule, options)]}
        elif not f.__name__ in f._rule_cache:
            f._rule_cache[f.__name__] = [(rule, options)]
        else:
            f._rule_cache[f.__name__].append((rule, options))
        return f
    return decorator


class AtomViews:
    prefix = None

    def __init__(self, application=None):
        self.views = None
        self.app = None

        if application:
            self.init_app(application)

    def init_app(self, application: Flask):
        self.app = application
        self.bind()

    @staticmethod
    def route(*args):
        route(args)

    def bind(self):
        views = [view for view in dir(self) if view.upper() in DEFAULT_METHOD_SET]
        prefix = self.prefix or self.__class__.__name__.split('Views').pop(0)
        blueprint = Blueprint(__name__, self.__class__.__name__)
        blueprint.url_prefix = f'/{prefix.lower()}'

        route_map = dict(
            index='',
            get='/<id>'
        )

        for view in views:
            func = getattr(self, view)
            blueprint.add_url_rule('', func.__name__, func, methods=[view.upper()])
            blueprint.add_url_rule('/', func.__name__, func, methods=[view.upper()])
        self.app.register_blueprint(blueprint)

    @classmethod
    def register(cls, app):
        instance = cls(app)
        instance.bind()
