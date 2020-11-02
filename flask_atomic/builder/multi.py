import secrets

from flask import Blueprint
from flask import request


from handyhttp import HTTPSuccess
from handyhttp import HTTPCreated
from handyhttp import HTTPDeleted
from handyhttp import HTTPSuccess
from handyhttp import HTTPBadRequest
from handyhttp import HTTPException
from handyhttp import HTTPNotFound

from sqlalchemy_blender import serialize
from sqlalchemy_blender import iserialize
from sqlalchemy_blender import QueryBuffer
from sqlalchemy_blender.helpers import related
from sqlalchemy_blender.helpers import columns
from sqlalchemy_blender.dao import ModelDAO


from .cache import link
from . import cache


def bind(blueprint, instance, methods, tenant=None):
    for key in cache.ROUTE_TABLE.keys():
        endpoint = getattr(instance, key, None)
        if not endpoint:
            continue
        view_function = endpoint
        for idx, dec in enumerate(blueprint.decorators or []):
            if idx == 0:
                view_function = dec
            else:
                view_function = view_function(dec)
            view_function = view_function(endpoint)

        for item in cache.ROUTE_TABLE[endpoint.__name__]:
            if item[1][0] in methods:
                url = item[0]
                new_rule = f'/{instance.model.__tablename__}/{url.split("/").pop()}'
                new_rule_with_slash = new_rule = f'/{instance.model.__tablename__}{url}'

                if new_rule.endswith('/'):
                    new_rule = new_rule[:-1]

                if not new_rule_with_slash.endswith('/'):
                    new_rule_with_slash = f'{new_rule_with_slash}/'

                allowed_methods = item[1]
                name = f'{endpoint.__name__}_{instance.model.__tablename__}'
                blueprint.add_url_rule(new_rule, name, view_function, methods=allowed_methods)
                blueprint.add_url_rule(new_rule_with_slash, name, view_function, methods=allowed_methods)
    return blueprint


class MultiModelBuilder(Blueprint):

    def __init__(self, models, prefix=None, decorators=None, dao=None, **kwargs):
        super().__init__(
            __name__,
            f'public-access-blueprint-{secrets.token_urlsafe()}'
        )
        self.decorators = decorators
        self.models = models
        self.key = None
        self.tenant = None
        self.dao = dao
        self.binds = []
        self.methods = ['GET', 'POST', 'PUT', 'DELETE']

        if prefix:
            self.url_prefix = prefix

        for key, value in kwargs.items():
            setattr(self, key, value)

        if type(decorators) not in [list, set, tuple]:
            self.decorators = decorators
            if decorators:
                self.decorators = [self.decorators]

        self.prepare()

    def set_local_error_handler(self):
        @self.app_errorhandler(Exception)
        def errors(error=None):
            if isinstance(error, HTTPException):
                return error.pack()
            raise error
        self.app_errorhandler(Exception)(errors)

    def extract_config_override(self, config):
        new_config = [config, self.dao, self.key]
        for idx, item in enumerate(['model', 'key', 'dao']):
            if item in config:
                new_config[idx] = config.get(item)
        return new_config

    def prepare(self):
        # first cycle through each of the assigned models
        for item in self.models:
            # then create route assignments as per global control
            # TODO: Extend to individual control configuration also
            if isinstance(item, dict):
                config = self.extract_config_override(item)
                routes = Routes(*config)
            else:
                routes = Routes(item, self.dao, self.key)
            bind(self, routes, self.methods)

        self.set_local_error_handler()


class Routes:

    def __init__(self, model, dao, key):
        self.model = model
        self.dao = dao
        self.key = key

    def json(self, data, *args, **kwargs):
        return iserialize(data, **kwargs)

    @link(url='/', methods=['GET'])
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

        # self.querystring()
        rels = related(self.model)
        query = QueryBuffer(self.model).all()
        return HTTPSuccess(self.json(query.data, **query.queryargs.__dict__))

    @link(url='/<int:modelid>', methods=['GET'])
    @link(url='/<path:modelid>', methods=['GET'])
    def one(self, modelid, *args, **kwargs):
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

        if isinstance(modelid, str) and modelid.endswith('/'):
            modelid = modelid.split('/').pop(0)

        query = QueryBuffer(self.model)
        resp = query.get(modelid, self.key)

        if not resp:
            raise HTTPNotFound()
        return HTTPSuccess(self.json(resp, **query.queryargs.__dict__))

    @link(url='/<path:modelid>/<path:resource>', methods=['GET'])
    def one_child_resource(self, modelid, resource, *args, **kwargs):
        query = QueryBuffer(self.model, auto=False).one(self.key, modelid)
        modeltree = resource.split('/')

        if len(modeltree):
            data = query.data
            for item in modeltree:
                if isinstance(data, int) or isinstance(data, str):
                    raise HTTPBadRequest(msg='Cannot query this data type')
                if isinstance(data, list):
                    data = data[int(item)]
                else:
                    data = getattr(data, item)

        if resource in columns(self.model, strformat=True):
            return HTTPSuccess({resource: getattr(query.data, resource)})
        child = getattr(self.model, resource).comparator.entity.class_
        return HTTPSuccess(
            self.json(QueryBuffer(child, auto=False).query.join(self.model.articles).all(), **query.queryargs.__dict__),
            __parent=self.json(query.data, **query.queryargs.__dict__)
        )

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
