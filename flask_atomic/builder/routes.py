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

from .cache import link
from . import cache


DEFAULT_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']


def bind(blueprint, methods, tenant=None):
    for key in cache.ROUTE_TABLE.keys():
        endpoint = getattr(blueprint, key, None)
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
                new_rule = url.rstrip('/')
                new_rule_with_slash = '{}/'.format(new_rule)

                if tenant:
                    new_rule = f'{tenant}/{new_rule}'
                    new_rule_with_slash = f'{tenant}{new_rule_with_slash}'

                allowed_methods = item[1]
                blueprint.add_url_rule(new_rule, endpoint.__name__, view_function, methods=allowed_methods)
                blueprint.add_url_rule(new_rule_with_slash, f'{endpoint.__name__}_slash', view_function, methods=allowed_methods)
    return blueprint


class RouteBuilder(Blueprint):

    def __init__(self, name, module, model, decorators=None, dao=None, **kwargs):
        super().__init__(name, module)
        self.decorators = decorators
        self.model = model
        self.query = None
        self.tenant = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if not dao:
            self.dao = ModelDAO(model)
        else:
            self.dao = dao(model)

        if type(decorators) not in [list, set, tuple]:
            self.decorators = decorators
            if decorators:
                self.decorators = [self.decorators]

        url = str(self.model.__tablename__).replace('_', '-')
        self.url_prefix = f'/{url}'
        self.key = model.__mapper__.primary_key[0].name

        if kwargs.get('lookup', None):
            key = model.__mapper__.primary_key[0].name
            self.key = getattr(self.model, kwargs.get('lookup'))
        self.delete_flag = False
        # self.bind(getattr(self, 'methods', None) or DEFAULT_METHODS)

    def _before_request(self):
        self.querystring()

    def bind(self, methods):
        bind(self, methods, self.tenant)

    def set_soft_delete(self, flag):
        self.delete_flag = flag

    def _payload(self):
        payload = request.json
        return payload

    def querystring(self):
        self.query = QueryBuffer(self.model, auto=True)
        return self.query

    def json(self, data, queryargs=None):
        relations = None
        if queryargs:
            relations = queryargs.rels
        return serialize(self.model, data, rels=relations)

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
        schema = getschema(self.model)
        return HTTPSuccess(self.json(query.data, queryargs=query.queryargs), schema=schema)

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

        if resource == self.model.__tablename__:
            return self.get(*args, **kwargs)

        query = QueryBuffer(self.model)
        data = query.get(resource, self.key)
        if not data:
            return HTTPNotFound().pack()
        return HTTPSuccess(serialize(self.model, data, rels=query.queryargs.rels))

    @link(url='/<int:resource>/<path:field>', methods=['GET'])
    def one_child_resource(self, resource, field, *args, **kwargs):
        query = QueryBuffer(self.model, auto=False).one(self.key, resource)
        modeltree = field.split('/')

        if len(modeltree):
            data = query.data
            for item in modeltree:
                if isinstance(data, list):
                    data = data[int(item)]
                else:
                    data = getattr(data, item)

        if resource in columns(self.model, strformat=True):
            return HTTPSuccess({resource: getattr(query.data, resource)})
        child = getattr(self.model, resource).comparator.entity.class_
        return HTTPSuccess(serialize(child, getattr(query.data, resource)))

    @link(url='/', methods=['POST'])
    def post(self, *args, **kwargs):
        try:
            instance = self.dao.create(self._payload(), **kwargs)
        except Exception as exc:
            raise HTTPConflict(str(exc))
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

