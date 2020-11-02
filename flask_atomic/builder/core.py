import secrets

from flask import current_app
from flask import Flask
from flask import Blueprint

from .routes import RouteBuilder

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


class BuilderCore:

    def __init__(self, app=None, decorators=None, prefix=None, session=None, tenant=None, lookup=None, **kwargs):
        self.application = app
        self.decorators = decorators
        self.prefix = prefix
        self.session = session
        self.tenant = tenant
        self.lookup = lookup
        self.model = kwargs.get('model', None)
        self.models = kwargs.get('models', None)
        self.methods = kwargs.get('methods', None)
        self.blueprint = None

        for item in {'model', 'models', 'methods', 'dao', 'session', 'prefix'}:
            if item in kwargs:
                del kwargs[item]

        self.kwargs = kwargs

        if not self.methods:
            self.methods = DEFAULT_METHOD_SET

        self.name = None
        if kwargs.get('name', None):
            self.name = kwargs.get('name')
            del kwargs['name']
            self.app = Blueprint(__name__, f'{self.name}-extra')

        if app is not None:
            self.init_app(app)

        # if self.model:
        #     self.register_methods(self.model, app, self.methods)

    def define_prefix(self, model):
        return f'{self.prefix or ""}/{model.__tablename__}'

    def register_methods(self, model, app, methods, dao=None):
        blueprint = RouteBuilder(
            self.name or model.__tablename__,
            __name__,
            model,
            self.decorators,
            dao=dao,
            lookup=self.lookup,
            tenant=self.tenant,
            **self.kwargs
        )
        blueprint.bind(methods)
        # build out routes for this model
        self.blueprint = blueprint
        # if app:
        #     app.register_blueprint(blueprint, url_prefix=self.define_prefix(model))

    def bind(self, application: Flask):
        if self.model:
            self.register_methods(self.model, application, self.methods)
            application.register_blueprint(self.blueprint, url_prefix=self.define_prefix(self.model))
            return self

        for model in self.models or []:
            methods = DEFAULT_METHOD_SET
            delete = True

            dao = None
            if isinstance(model, tuple):
                methods = model[1].get('methods')
                if not methods:
                    methods = ['GET', 'POST', 'PUT', 'DELETE']
                delete = model[1].get('delete')
                dao = model[1].get('dao', None)
                model = model[0]

            self.register_methods(model, application, methods, dao)
            continue

            blueprint = RouteBuilder(
                model.__tablename__,
                __name__, model,
                self.decorators,
                dao=dao,
                lookup=self.lookup,
                tenant=self.tenant
            )

            if delete:
                blueprint.set_soft_delete(delete)
            blueprint.bind(methods)
            # build out routes for this model
            application.register_blueprint(blueprint, url_prefix=self.prefix)

    def init_app(self, application: Flask):
        self.models = current_app.config.get('ATOMIC_MODELS', None)
        application.teardown_appcontext(self.teardown)
        self.bind(application)

    def teardown(self, exc):
        self.models = set()
