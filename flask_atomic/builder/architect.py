import secrets
import logging

from collections.abc import Iterable

from flask import Flask
from flask import Blueprint
from flask import request
from flask_atomic.builder import cache
from sqlalchemy_blender.dao import ModelDAO
from handyhttp.exceptions import HTTPException

from .endpoints import Routes


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']


def bind(blueprint, routes, methods, prefix=None):
    for key in cache.ROUTE_TABLE.keys():
        endpoint = getattr(routes, key, None)
        if not endpoint:
            continue
        view_function = endpoint
        for idx, dec in enumerate(blueprint.decorators or []):
            if idx == 0:
                view_function = dec
            else:
                view_function = view_function(dec)
            view_function = view_function(endpoint)

        for idx, item in enumerate(cache.ROUTE_TABLE[endpoint.__name__]):
            if item[1][0] in methods:
                url = item[0]
                new_rule = url.rstrip('/')
                new_rule_with_slash = '{}/'.format(new_rule)

                if prefix:
                    new_rule = f'{prefix}{new_rule}'
                    new_rule_with_slash = f'{prefix}{new_rule_with_slash}'

                allowed_methods = item[1]
                name = f'{prefix}-{idx}-{endpoint.__name__}'
                blueprint.add_url_rule(new_rule, name, view_function, methods=allowed_methods)
                blueprint.add_url_rule(new_rule_with_slash, f'{name}_slash', view_function, methods=allowed_methods)
    return blueprint


class Architect(Blueprint):

    def __init__(self, models, decorators=None, dao=ModelDAO, **kwargs):
        super().__init__(
            f'blueprint-{secrets.token_urlsafe()}',
            __name__,
        )
        self.decorators = decorators

        if not isinstance(models, Iterable):
            models = [models]

        self.models = models
        self.override = None
        self.key = kwargs.get('lookup', None)
        self.tenant = None
        self.dao = dao
        self.throw = False
        self.binds = []
        self.logging = True
        self.pre = False
        self.errors = True
        self.suffix = True
        self.methods = ['GET', 'POST', 'PUT', 'DELETE']
        self.static_url_path = None

        if kwargs.get('prefix', None):
            self.url_prefix = kwargs.get('prefix', None)

        for key, value in kwargs.items():
            setattr(self, key, value)

        if type(decorators) not in [list, set, tuple]:
            self.decorators = decorators
            if decorators:
                self.decorators = [self.decorators]

    def link(self, app: Flask):
        self.prepare()

        if self.errors:
            @self.errorhandler(Exception)
            def catch_error(exception):
                if self.throw:
                    raise exception
                if isinstance(exception, HTTPException):
                    return exception.pack()
                raise exception

        @self.before_request
        def preprocess(*args, **kwargs):
            if self.pre:
                getattr(self, 'pre')()
            self.log()

        app.register_blueprint(self)

    def extract_config_override(self, config):
        new_config = [config, self.dao, self.key, []]
        for idx, item in enumerate(['model', 'dao', 'key', 'methods']):
            if item in config:
                new_config[idx] = config.get(item)
        return new_config

    def log(self, log=None):
        if self.logging:
            if not log:
                logger.info(request.base_url)

    def prepare(self):
        # first cycle through each of the assigned models
        for item in self.models:
            routes: Routes
            methods = self.methods
            # then create route assignments as per global control
            # TODO: Extend to individual control configuration also
            if isinstance(item, dict):
                config = self.extract_config_override(item)
                routes = Routes(*config, response=self.response)
                prefix = f'{item.get("model").__tablename__}'
                methods = item.get('methods', None) or self.methods
            else:
                primary = item.__mapper__.primary_key[0].name
                routes = Routes(item, self.dao(item), self.key or primary, response=self.response)
                prefix = f'{item.__tablename__}'
            if len(self.models) == 1 and not self.suffix:
                prefix = ''
            bind(self, routes, methods, prefix=prefix)

    def error_handler(self, exception):
        return exception.pack()

    def response(self, response):
        return response

    def exception(self, exception):
        if self.exception:
            return self.exception(exception)
        if self.throw:
            raise exception
        return exception
