import json

from flask import request

from sqlalchemy_blender import QueryBuffer
from sqlalchemy_blender.helpers import iserialize

from handyhttp.responses import HTTPSuccess
from handyhttp.responses import HTTPCreated
from handyhttp.responses import HTTPUpdated
from handyhttp.responses import HTTPDeleted
from handyhttp.exceptions import HTTPConflict
from handyhttp.exceptions import HTTPBadRequest
from handyhttp.exceptions import HTTPNotFound
from handyhttp.exceptions import HTTPNotProcessable

# from flask_atomic.helpers import session
from .cache import link


class DynamoRoutes:
    pass


class Routes:

    def __init__(self, model, dao, key, throw=True, response=None):
        self.model = model
        self.dao = dao
        self.key = key
        self.throw = throw
        self.response = response

    def payload(self):
        return json.loads(request.data)

    def exception(self, exception):
        raise exception

    def json(self, data, *args, **kwargs):
        if isinstance(data, list) and len(data) and isinstance(data[0], tuple):
            _json = []
            for item in data:
                _json.append({key: getattr(item, key, None) for key in item._fields})
            return _json
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

        if not resp.data:
            return self.exception(HTTPNotFound())
        return self.response(HTTPSuccess(self.json(query.data, **query.queryargs.__dict__)))

    @link(url='/<resource>/<path:field>', methods=['GET'])
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
        if not payload:
            self.exception(HTTPNotProcessable(msg='Invalid request payload.'))
        instance = self.dao.create(payload, **kwargs)
        self.dao.save(instance)
        return HTTPCreated(self.json(instance))

    @link(url='/<resource>/<field>/', methods=['POST'])
    def post_child_resource(self, resource, field, *args, **kwargs):
        instance = QueryBuffer(self.model).one(self.key, resource).data
        child = getattr(self.model.__mapper__.relationships, field).entity.entity(**self.payload())
        getattr(instance, field).append(child)
        self.dao.save(instance)
        return HTTPUpdated()

    @link(url='/<resource>', methods=['DELETE'])
    def delete(self, resource, *args, **kwargs):
        instance = QueryBuffer(self.model).one(self.key, resource)
        if not instance.data:
            raise HTTPNotFound()

        if self.dao:
            self.dao.delete(instance.data)
        return self.response(HTTPSuccess())

    @link(url='/<resource>', methods=['PUT'])
    def put(self, resource, *args, **kwargs):
        query = QueryBuffer(self.model).one(self.key, resource)
        instance = query.data
        payload = self.payload()
        self.dao.update(instance, payload)
        return self.response(HTTPUpdated(iserialize(instance)))
