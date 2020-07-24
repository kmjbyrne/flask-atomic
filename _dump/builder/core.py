from flask import current_app
from flask import Flask

from .routes import RouteBuilder


DEFAULT_METHOD_SET = ['GET', 'POST', 'PUT', 'DELETE']


class BuilderCore:
    models: set

    def __init__(self, application=None, decorators=None, prefix=None):
        self.application = application
        self.decorators = decorators
        self.prefix = prefix

        if application is not None:
            self.init_app(application)

    def bind(self, application: Flask):
        for model in self.models:
            methods = DEFAULT_METHOD_SET
            delete = True
            if isinstance(model, tuple):
                methods = model[1].get('methods')
                delete = model[1].get('delete')
                model = model[0]

            blueprint = RouteBuilder(model.__tablename__, __name__, model, self.decorators, prefix=self.prefix)

            if delete:
                blueprint.set_soft_delete(delete)
            blueprint.bind(methods)
            # build out routes for this model
            application.register_blueprint(blueprint)

    def init_app(self, application: Flask):
        self.models = current_app.config.get('ATOMIC_MODELS', None)
        application.teardown_appcontext(self.teardown)
        self.bind(application)

    def teardown(self, exc):
        self.models = set()
