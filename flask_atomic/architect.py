import secrets

from collections.abc import Iterable

from flask import Flask
from flask import Blueprint
from flask import request

from sqlalchemy_blender import QueryBuffer
from sqlalchemy_blender.helpers import related
from sqlalchemy_blender.helpers import serialize
from sqlalchemy_blender.helpers import iserialize
from sqlalchemy_blender.helpers import columns
from sqlalchemy_blender.helpers import getschema
from sqlalchemy_blender.dao import ModelDAO

from handyhttp.responses import HTTPSuccess
from handyhttp.responses import HTTPCreated
from handyhttp.responses import HTTPUpdated
from handyhttp.responses import HTTPDeleted
from handyhttp.exceptions import HTTPConflict
from handyhttp.exceptions import HTTPNotFound
from handyhttp.exceptions import HTTPBadRequest
from handyhttp.exceptions import HTTPException

from flask_atomic.builder.cache import link
from flask_atomic.builder import cache


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

    def __init__(self, models, decorators=None, dao=None, **kwargs):
        super().__init__(
            f'blueprint-{secrets.token_urlsafe()}',
            __name__,
        )
        self.decorators = decorators

        if not isinstance(models, Iterable):
            models = [models]

        self.models = models
        self.override = None
        self.key = None
        self.tenant = None
        self.dao = dao
        self.throw = True
        self.binds = []
        self.methods = ['GET', 'POST', 'PUT', 'DELETE']

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
        @self.errorhandler(Exception)
        def catch_error(exception):
            if isinstance(exception, HTTPException):
                return exception.pack()
            raise exception
        app.register_blueprint(self)

    def extract_config_override(self, config):
        new_config = [config, self.dao, self.key]
        for idx, item in enumerate(['model', 'key', 'dao']):
            if item in config:
                new_config[idx] = config.get(item)
        return new_config

    def prepare(self):
        # first cycle through each of the assigned models
        for item in self.models:
            routes: Routes
            primary = item.__mapper__.primary_key[0].name
            # then create route assignments as per global control
            # TODO: Extend to individual control configuration also
            if isinstance(item, dict):
                config = self.extract_config_override(item)
                routes = Routes(*config)
            else:
                routes = Routes(item, self.dao, self.key or primary, response=self.response)
            prefix = f'{item.__tablename__}'
            if len(self.models) == 1:
                prefix = ''
            bind(self, routes, self.methods, prefix=prefix)

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


class Routes:

    def __init__(self, model, dao, key, throw=True, response=None, exception=None):
        self.model = model
        self.dao = dao
        self.key = key
        self.throw = throw
        self.response = response
        self.exception = exception

    def json(self, data, *args, **kwargs):
        return iserialize(data, **kwargs)

    @link(url='', methods=['GET'])
    def get(self, *args, **kwargs):
        """
        The principal GET handler for the RouteBuilder. All GET requests that are
        structured like so:

        `HTTP GET http://localhost:5000/<prefix>/<route-model>`

        (Where your-blueprint represents a particular resource mapping).

        Will be routed to this function. This will use the RouteBuilder DAO
        and then fetch data for the assigned model. In this case, select all.

        :return: response object with application/json content-type preset.
        :rtype: HTTPSuccess
        """

        query = QueryBuffer(self.model).all()
        return self.response(HTTPSuccess(self.json(query.data, **query.queryargs.__dict__)))

    @link(url='/<resource>', methods=['HEAD'])
    def head(self, resource):
        query = QueryBuffer(self.model)
        resp = query.one(self.key, resource)

        if not resp:
            return self.exception(HTTPNotFound())
        return HTTPSuccess()

    @link(url='/<resource>', methods=['GET'])
    def one(self, resource, *args, **kwargs):
        """
        The principal GET by ID handler for the RouteBuilder. All GET requests
        that are structured like so:

        `HTTP GET http://localhost:5000/<prefix>/<route-model>/<uuid>`

        (Where <your-blueprint> represents a particular resource mapping).

        (Where <uuid> represents an database instance ID).

        This will use the RouteBuilder DAO and then fetch data for the
        assigned model. In this case, selecting only one, by UUID.

        :return: response object with application/json content-type preset.
        :rtype: Type[JsonResponse]
        """

        if isinstance(resource, str) and resource.endswith('/'):
            resource = resource.split('/').pop(0)

        query = QueryBuffer(self.model)
        resp = query.one(self.key, resource)

        if not resp:
            return self.exception(HTTPNotFound())

        return self.response(HTTPSuccess(self.json(query.data, **query.queryargs.__dict__)))

    @link(url='/<resource>/<string:field>', methods=['GET'])
    def one_child_resource(self, resource, field, *args, **kwargs):
        query = QueryBuffer(self.model, auto=False).one(self.key, resource)
        instance = query.one(self.key, resource).data
        path = field.split('/')
        prop = None

        if not instance:
            return self.exception(HTTPNotFound())

        if len(path) > 1:
            child = None
            data = query.data
            endpoint = path.pop()
            for idx, item in enumerate(path):
                if isinstance(data, int) or isinstance(data, str):
                    raise HTTPBadRequest(msg='Cannot query this data type')
                if isinstance(data, list):
                    child = data[int(item)]
                else:
                    child = getattr(instance, item)
            data = getattr(child, endpoint)
            prop = endpoint
        else:
            prop = field
            data = getattr(instance, field)

        return HTTPSuccess({prop: data}, path=field.split('/'))

    @link(url='/', methods=['POST'])
    def post(self, *args, **kwargs):
        payload = request.json
        instance = self.dao.create(payload, **kwargs)
        return HTTPCreated(self.json(instance))

    @link(url='/<int:modelid>/<resource>/', methods=['POST'])
    def post_child_resource(self, modelid, resource, *args, **kwargs):
        instance = QueryBuffer(self.model).one(self.key, modelid).data
        child = getattr(self.model.__mapper__.relationships, resource).entity.entity(**self._payload())
        getattr(instance, resource).append(child)
        dao = self.dao.save(instance)
        return HTTPUpdated()

    @link(url='/<int:modelid>', methods=['DELETE'])
    def delete(self, modelid, *args, **kwargs):
        if self.delete:
            self.dao.delete(self.dao.one(modelid)) #, self.delete_flag)
        else:
            self.dao.delete(self.dao.one(modelid))
        return HTTPDeleted()

    @link(url='/counts/<int:modelid>', methods=['DELETE'])
    def count(self):
        pass

    @link(url='/<int:modelid>', methods=['PUT'])
    def put(self, modelid, *args, **kwargs):
        query = QueryBuffer(self.model).one(self.key, modelid)
        instance = query.data
        self.dao.update(instance, self._payload())
        return HTTPUpdated(iserialize(instance))
