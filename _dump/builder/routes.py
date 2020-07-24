import json

from flask import Blueprint
from flask import request


from flask_atomic.query.buffer import QueryBuffer
from ..orm.helpers import getschema
from ..orm.helpers import serialize
from flask_atomic.http.responses import HTTPSuccess
from flask_atomic.http.responses import HTTPCreated
from flask_atomic.http.responses import HTTPUpdated
from flask_atomic.http.responses import HTTPDeleted
from .cache import link
from .dao import ModelDAO
from . import cache


def bind(blueprint, methods):
    for key in cache.ROUTE_TABLE.keys():
        endpoint = getattr(blueprint, key, None)
        if not endpoint:
            continue
        view_function = endpoint
        for idx, dec in enumerate(blueprint.decorators):
            if idx == 0:
                view_function = dec
            else:
                view_function = view_function(dec)
            view_function = view_function(endpoint)

        for item in cache.ROUTE_TABLE[endpoint.__name__]:
            if item[1][0] in methods:
                url = item[0]
                allowed_methods = item[1]
                blueprint.add_url_rule(url, endpoint.__name__, view_function, methods=allowed_methods)
    return blueprint


class RouteBuilder(Blueprint):

    def __init__(self, name, module, model, decorators, **kwargs):
        super().__init__(name, module)
        self.decorators = decorators
        self.model = model
        self.dao = ModelDAO(model)
        if type(decorators) not in [list, set, tuple]:
            self.decorators = [self.decorators]

        url = str(self.model.__tablename__).replace('_', '-')
        self.url_prefix = f'/{url}'
        self.key = model.__mapper__.primary_key[0].name
        self.delete_flag = False

    def bind(self, methods):
        bind(self, methods)

    def set_soft_delete(self, flag):
        self.delete_flag = flag

    def _payload(self):
        payload = json.loads(request.data)
        return payload

    def json(self, data):
        return serialize(self.model, data)

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

        query = QueryBuffer(self.model).all()
        schema = getschema(self.model)
        return HTTPSuccess(self.json(query.data), schema=schema)

    @link(url='/<int:modelid>', methods=['GET'])
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

        query = QueryBuffer(self.model).one(self.key, modelid)
        schema = getschema(self.model)
        return HTTPSuccess(self.json(query.data), schema=schema)

    @link(url='/', methods=['POST'])
    def post(self, *args, **kwargs):
        """
        Create a new user
        ---
        tags:
        - users
        definitions:
        - schema:
         id: Group
         properties:
           name:
            type: string
            description: the group's name
        parameters:
        - in: body
        name: body
        schema:
         id: User
         required:
           - email
           - name
         properties:
           email:
             type: string
             description: email for user
           name:
             type: string
             description: name for user
           address:
             description: address for user
             schema:
               id: Address
               properties:
                 street:
                   type: string
                 state:
                   type: string
                 country:
                   type: string
                 postalcode:
                   type: string
           groups:
             type: array
             description: list of groups
             items:
               $ref: "#/definitions/Group"
        responses:
        200:
        description: User created
        """

        instance = self.dao.create(self._payload())
        return HTTPCreated(self.json(instance))

    @link(url='/<int:modelid>', methods=['DELETE'])
    def delete(self, modelid, *args, **kwargs):
        if self.delete:
            self.dao.softdelete(self.dao.one(modelid), self.delete_flag)
        else:
            self.dao.delete(self.dao.one(modelid))
        return HTTPDeleted()

    @link(url='/<int:modelid>', methods=['PUT'])
    def put(self, modelid, *args, **kwargs):
        instance = QueryBuffer(self.model).one(self.key, modelid).data
        self.dao.update(instance, self._payload())
        return HTTPUpdated()
