from functools import partial
from typing import Optional
from typing import Type

from flask import Blueprint
from flask import jsonify
from flask import request

from flask_atomic.blueprint.decorators import default_decorator
from flask_atomic.dao.base import BaseDAO
from flask_atomic.httputils.responses import JsonBadRequestResp
from flask_atomic.httputils.responses import JsonDeletedResp
from flask_atomic.httputils.responses import JsonNotFoundResp
from flask_atomic.httputils.responses import JsonOKResponse
from flask_atomic.httputils.responses import json_response
from flask_atomic.orm.base import DeclarativeBase

UUID = 'uuid'
ACCEPTED_METHODS = ['GET', 'POST', 'PUT', 'DELETE']


class CoreBlueprint(Blueprint):
    """
    CoreBlueprint class. Extends the base Flask Blueprint class.

    Adds some boilerplate endpoints for GET, POST, PUT, DELETE for interacting
    with models and abstracting a lot of code away.

    The class is meant to be used as a soft plugin, so none of the core features
    are taken away from the base Flask Blueprint.

    """

    def __init__(self, name, module, model, dao=None, decorator=None, methods=None, url_prefix=None, lookupkey=None):
        # Make sure super call stays on top. Otherwise Blueprint functions are inaccessible
        super().__init__(name, module)

        if url_prefix:
            self.url_prefix = url_prefix

        if model is None:
            raise AttributeError('CoreBlueprint requires a model instance.')

        if decorator is None:
            decorator = default_decorator
        self.decorator = decorator

        if lookupkey is None:
            lookupkey = model.identify_primary_key()

        self.lookupkey = lookupkey

        self.methods = methods
        if methods is None:
            self.methods = list()

        # !!!: Order matters here
        self.model = model
        self.dao = self.__set_dao(dao, model)
        self.__register_principal_endpoints()

    def allhttp(self):
        self.methods = ACCEPTED_METHODS

    def set_dao(self, dao: Optional[BaseDAO], model: Type[DeclarativeBase]) -> Type[BaseDAO]:
        return self.__set_dao(dao, model)

    def __set_dao(self, dao: Optional[BaseDAO], model: Type[DeclarativeBase]) -> Type[BaseDAO]:
        """
        Function for setting up the data access object (DAO) and ensuring that
        the default DAO is setup, if none provided (most common scenario).

        :param dao: Data access object to be assigned to this Blueprint.
        :type dao: Type[BaseDAO], optional

        :param model: Data access object to be assigned to this Blueprint.
        :type model: Type[DeclarativeBase]

        :return: Constructed data access object with model assignment
        :rtype: Type[BaseDAO]
        """

        if model is None:
            raise AttributeError('CoreBlueprint requires a model instance.')

        if dao is None:
            dao = BaseDAO
        dao.model = model
        return dao

    def default_handler(self, path: str):
        """
        This is the default route handler, if the endpoint regex check fails for
        other endpoints, then this will become the endpoint to use.

        :param path: the full path from Blueprint prefix to endpoint.
        :return:
        """

        # TODO: Complete this function. Allowing for any path? Maybe not advised.
        # Bit of padding requirement to help to dictate its usage.

        depth = path.split('/')
        return jsonify(path=f"%{self.name} : ".join(depth))

    def __dao_query_forwarder(self, query, arg=None):
        return query(arg)

    def __default_get_request(self, **kwargs) -> Type[json_response]:
        """
        The principal GET handler for the CoreBlueprint. All GET requests that are
        structured like so:
        
        `HTTP GET http://localhost:5000/api/<your-blueprint>`

        (Where your-blueprint represents a particular resource mapping).
        
        Will be routed to this function. This will use the CoreBlueprints DAO
        and then fetch data for the assigned model. In this case, select all.
        
        :return: response object with application/json content-type preset.
        :rtype: Type[JsonResponse]
        """

        dao = self.dao(self.model, querystring=request.args).autoquery()
        buffer = self.__dao_query_forwarder(dao.query().all)
        try:
            content = dict(data=buffer.json(exclude=dao.queryargs.exclusions), schema=buffer.schema)
            return JsonOKResponse(content)
        except AttributeError as error:
            return JsonBadRequestResp(message=str(error))

    def __default_get_one_request(self, uuid: str) -> Type[json_response]:
        """
        The principal GET by ID handler for the CoreBlueprint. All GET requests
        that are structured like so:

        `HTTP GET http://localhost:5000/api/<your-blueprint>/<uuid>`

        (Where <your-blueprint> represents a particular resource mapping).

        (Where <uuid> represents an database instance ID).

        This will use the CoreBlueprints DAO and then fetch data for the
        assigned model. In this case, selecting only one, by UUID.

        :return: response object with application/json content-type preset.
        :rtype: Type[JsonResponse]
        """

        dao = self.dao(self.model, querystring=request.args).autoquery()
        query = partial(dao.get_one_by, self.lookupkey, uuid)
        buffer = self.__dao_query_forwarder(query)
        buffer.relationships = dao.queryargs.rels

        if buffer.data is None:
            return JsonNotFoundResp()
        try:
            content = dict(data=buffer.json(exclude=dao.queryargs.exclusions), schema=buffer.schema)
            return JsonOKResponse(content)
        except AttributeError as error:
            return JsonBadRequestResp(message=str(error))

    def __default_get_field_request(self, uuid: int, field: str) -> Type[json_response]:
        """
        The principal GET.Field handler for the CoreBlueprint. All GET requests
        that are structured like so:

        `HTTP GET http://localhost:5000/api/<your-blueprint>/<uuid>/<some-field>`

            (Where <your-blueprint> represents a particular resource mapping).

            (Where <uuid> represents an database instance ID).

            (Where <your-field> represents an individual field on a model).

        This will use the CoreBlueprints DAO and then fetch data for the assigned
        model. In this case, selecting one, based on ID. Then it will extract
        the field specified, and return the field as a singlet object:

        `field->value`

        :return: response object with application/json content-type preset.
        :rtype: Type[JsonResponse]
        """

        dao = self.dao(self.model, querystring=dict(request.args))
        buffer = self.__dao_query_forwarder(dao.get_one, uuid)

        if buffer.data is None:
            return JsonNotFoundResp()
        if uuid is None or field is None:
            return JsonNotFoundResp()

        try:
            return JsonOKResponse({field: getattr(buffer.view(), field)})
        except AttributeError:
            return JsonNotFoundResp(dict(error=f'{field} is not a valid field'))

    def __default_post_request(self, **kwargs) -> Type[json_response]:
        """
        The principal POST handler for the CoreBlueprint. All POST requests
        that are structured like so:

        `HTTP POST http://localhost:5000/api/<your-blueprint>`

        Including the POST request body:

        {
            **key: **value
        }

        Values for the model are provided in JSON format.

        (Where <your-blueprint> represents a particular resource mapping).

        This will use the CoreBlueprints DAO and then create an instance of the
        assigned model. The the function will bind this to a session, and then
        create an instance in the database.

        This function requires a payload, however this is not a function arg,
        rather it is an arg bound to the request object.

        :return: response object with application/json content-type preset.
        :rtype: Type[JsonResponse]
        """

        dao = self.dao(self.model, querystring=dict(request.args))
        payload = request.json
        if 'id' in payload.keys():
            del payload['id']

        try:
            buffer = dao.create(payload)
        except ValueError as error:
            return JsonBadRequestResp(error=str(error))
        content = dict(message='{} created!'.format(buffer.name()), data=buffer.json())
        return JsonOKResponse(content)

    def __default_delete_request(self, uuid: int, **kwargs) -> Type[json_response]:

        """
        The principal DELETE handler for the CoreBlueprint. All DELETE requests
        that are structured like so:
    
        `HTTP POST http://localhost:5000/api/<your-blueprint>/<uuid>`
    
        (Where <your-blueprint> represents a particular resource mapping).
    
        (Where <uuid> presents the database instance ID).
    
        This will use the CoreBlueprints DAO and then delete the instance of the
        assigned model. The the function will bind this to a session, and then
        execute the removal instruction. By default, this removal consists of
        setting the database entry status to 'D'.
    
        :return: response object with application/json content-type preset.
        :rtype: Type[JsonResponse]
        """

        dao = self.dao(self.model, querystring=dict(request.args))
        try:
            self.__dao_query_forwarder(dao.sdelete, uuid)
        except Exception as error:
            return JsonBadRequestResp(error=str(error))
        return JsonDeletedResp()

    def __default_put_request(self, uuid: int, **kwargs) -> Type[json_response]:
        """
        The principal PUT handler for the CoreBlueprint. All PUT requests
        that are structured like so:
    
        `HTTP POST http://localhost:5000/api/<your-blueprint>/<uuid>`
    
        (Where <your-blueprint> represents a particular resource mapping).
    
        (Where <uuid> presents the database instance ID).
    
        This will use the CoreBlueprints DAO and then update the instance of the
        assigned model. The the function will bind this to a session, and then
        execute the update instruction. Updates will occur based on the values
        provided. The entire instance is not required.
    
        :return: response object with application/json content-type preset.
        :rtype: Type[JsonResponse]
        """

        dao = self.dao(self.model, querystring=dict(request.args))
        buffer = dao.get_one(uuid)
        payload = request.json

        try:
            dao.iupdate(buffer.view(), uuid, payload)
            content = dict(data=buffer.json(), schema=dao.schema())
            return JsonOKResponse(content)
        except Exception as error:
            return JsonBadRequestResp(error=str(error))
        except AssertionError as validationerr:
            return jsonify(error=validationerr), 400

    def __register_principal_endpoints(self) -> None:
        # r = Route, m = HTTP method, h = handler function for the endpoint
        # TODO: Might break this out into an operations class later
        route_table = [
            dict(route='', method='GET', hdl=self.__default_get_request),
            dict(route=f'/<{UUID}>', method='GET', hdl=self.__default_get_one_request),
            dict(route=f'/<{UUID}>/<field>', method='GET', hdl=self.__default_get_field_request),
            dict(route='/', method='POST', hdl=self.__default_post_request),
            dict(route=f'/<{UUID}>', method='DELETE', hdl=self.__default_delete_request),
            dict(route=f'/<{UUID}>', method='PUT', hdl=self.__default_put_request),
            # dict(r='/<path:path>', m='GET', h=self.default_handler),
        ]

        for item in list(filter(lambda r: r.get('method') in self.methods, route_table)):
            method = str(item.get('method'))
            view_func = self.decorator(item.get('hdl'))
            self.add_url_rule(
                item.get('route'),
                item.get('hdl').__name__,
                view_func,
                methods=[method],
                strict_slashes=False
            )
