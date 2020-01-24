from flask import jsonify
from flask import Blueprint
from flask import request
from flask_electron.dao.base import BaseDAO
from flask_electron.http.responses import JsonOKResponse
from flask_electron.logger import get_logger

logger = get_logger(__name__)


class CoreBlueprint(Blueprint):

    def __init__(self, name, module, dao=None, model=None, decorator=None):
        if dao is None:
            self.dao = BaseDAO
            self.dao.model = model

        if decorator is None:
            def _dec(func):
                def __dec(*args, **kwargs):
                    return func(*args, **kwargs)

                return __dec

            decorator = _dec

        self.decorator = decorator
        self.dao = dao
        self.model = model
        super().__init__(name, module)
        self.register_generic_routes()

    def get_handler_name(self):
        return '{}_{}'.format(self.name, 'get')

    def default_handler(self, path: str):
        depth = path.split('/')
        return jsonify(path=f"%{self.name} : ".join(depth))

    def default_get_request(self) -> object:
        dao = self.dao(querystring=dict(request.args))
        buffer = dao.query().all()
        return jsonify(data=buffer.json(), schema=dao.schema()), 200

    def default_get_one_request(self, uuid: int) -> tuple:
        dao = self.dao()
        buffer = dao.get_one(uuid)
        if buffer.data is None:
            return jsonify(error='Resource not found'), 404
        return JsonOKResponse(data=buffer.json(), schema=dao.schema())

    def default_get_field_request(self, uuid: int, field: str) -> tuple:
        buffer = self.dao().get_one(uuid)

        if buffer.data is None:
            return jsonify(data=dict(), schema=buffer.schema), 404

        if uuid is None or field is None:
            return jsonify(error='Invalid selection'.format(field)), 404

        try:
            return JsonOKResponse(getattr(buffer.view(), field))
        except AttributeError:
            return jsonify(error='{} is not a valid field'.format(field)), 404

    def default_post_request(self, *args, **kwargs):
        payload = request.json
        try:
            instance = self.dao().create(payload)
        except ValueError as error:
            return jsonify(error=str(error))
        except Exception as error:
            return jsonify(error=str(error))
        return jsonify(message='{} created!'.format(instance.name()), data=instance.json()), 200

    def default_delete_request(self, uuid: int, *args, **kwargs):
        try:
            self.dao().sdelete(uuid)
        except Exception as error:
            return jsonify(error=str(error)), 401
        return jsonify(message='Item successfully marked for deletion'), 202

    def default_put_request(self, uuid: int, *args, **kwargs):
        try:
            instance = self.dao().update(uuid)
        except Exception as error:
            return jsonify(error=str(error)), 401
        return jsonify(instance), 200

    def register_generic_routes(self):
        route_table = [
            dict(route='', method='GET', handler=self.default_get_request),
            dict(route='/<uuid>', method='GET', handler=self.default_get_one_request),
            dict(route='<path:path>', method='GET', handler=self.default_handler),
            dict(route='/<uuid>/<field>', method='GET', handler=self.default_get_field_request),
            dict(route='', method='POST', handler=self.default_post_request),
            dict(route='/<uuid>', method='DELETE', handler=self.default_delete_request),
            dict(route='/<uuid>', method='PUT', handler=self.default_put_request),
        ]

        for item in route_table:
            method = str(item.get('method'))
            view_func = self.decorator(item.get('handler'))
            self.add_url_rule(item.get('route'), item.get('handler').__name__, view_func, methods=[method])

        return self
