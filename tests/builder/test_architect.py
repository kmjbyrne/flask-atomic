import unittest

from flask import Flask
from flask import request
from functools import wraps
from handyhttp import HTTPSuccess
from handyhttp import HTTPForbidden

from flask_atomic import Architect
from tests.fixtures.fixtures import FIXED_TABLENAME
from tests.fixtures.fixtures import SECOND_TABLENAME
from tests.fixtures.fixtures import ExampleModel
from tests.fixtures.fixtures import AnotherModel
from tests.fixtures.fixtures import CustomDAO
from tests.fixtures.fixtures import db


class BaseAppTest(unittest.TestCase):
    def setUp(self) -> None:
        self.flask = Flask(__name__)
        db.init_app(self.flask)

        self.blueprint = Architect(ExampleModel, prefix='/test')
        self.blueprint.link(self.flask)
        self.client = self.flask.test_client()
        self.expected = {'data': {'id': 1, 'label': 'test', 'related_id': None, 'state': 'Y'}}
        self.second = {'data': {'id': 1, 'label': 'test', 'related_id': 1, 'state': 'Y'}}

        with self.flask.app_context():
            db.create_all()
            entity = AnotherModel(label='test')
            db.session.add(entity)
            db.session.commit()

    def create(self):
        with self.flask.app_context():
            other = AnotherModel(label='test')
            db.session.add(other)
            entity = ExampleModel(label='test')
            entity.related_id = 1
            db.session.add(entity)
            db.session.commit()

    def setup(self):
        self.blueprint.link(self.flask)
        self.client = self.flask.test_client()
        with self.flask.app_context():
            db.create_all()


class TestBlueprintFunctionality(BaseAppTest):

    def test_blueprint_with_config(self):
        config = [dict(model=ExampleModel, key=ExampleModel.id.name, dao=CustomDAO(ExampleModel), methods=['POST'])]
        self.blueprint = Architect(config, prefix='/methods-test', errors=False)
        self.blueprint.link(self.flask)
        resp = self.client.post('/methods-test', json={'label': 'test'})
        self.assertEqual(resp.json, {'data': {'id': 1, 'label': 'different value than posted', 'related_id': None, 'state': 'Y'}})

        resp = self.client.get('/methods-test', json={'label': 'test'})
        self.assertEqual(resp.status_code, 405)

    def test_blueprint_with_config_delete(self):
        config = [dict(model=ExampleModel, key=ExampleModel.id.name, dao=CustomDAO(ExampleModel), methods=['DELETE'])]
        self.blueprint = Architect(config, prefix='/methods-test', errors=False)
        self.blueprint.link(self.flask)
        self.create()
        resp = self.client.delete('/methods-test/1', json={'label': 'test'})
        self.assertEqual(resp.json.get('data').get('state'), 'D')

    def test_blueprint_explicit_methods(self):
        self.blueprint = Architect(ExampleModel, prefix='/methods-test', methods=['GET'])
        self.blueprint.link(self.flask)
        resp = self.client.post('/methods-test', json={'label': 'test'})
        self.assertEqual(resp.status_code, 405)

        resp = self.client.delete('/methods-test/1', json={'label': 'test'})
        self.assertEqual(resp.status_code, 405)

        resp = self.client.put('/methods-test/1', json={'label': 'test'})
        self.assertEqual(resp.status_code, 405)

        resp = self.client.head('/methods-test/1', json={'label': 'test'})
        self.assertEqual(resp.status_code, 404)

    def test_blueprint_extends_ok(self):
        self.blueprint = Architect(ExampleModel, prefix='/test-blueprint')
        @self.blueprint.route('/test-path')
        def endpoint():
            return HTTPSuccess()

        self.setup()
        resp = self.client.get('/test-blueprint/test-path')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/test-blueprint/non-test-path')
        self.assertEqual(resp.status_code, 404)

    def test_blueprint_overrides(self):
        def response_override(*args, **kwargs):
            return HTTPSuccess(data='Test', message='Override')

        self.blueprint = Architect(ExampleModel, prefix='/test-blueprint', response=response_override)
        self.setup()
        resp = self.client.get('/test-blueprint')
        self.assertEqual(resp.json, {'data': 'Test', 'message': 'Override'})

        resp = self.client.get('/test-blueprint/404-route')
        self.assertEqual(resp.status_code, 404)


class TestArchitect(BaseAppTest):

    def test_index(self):
        resp = self.client.get(f'/test')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'data': []})

    def test_multiple_models_indices(self):
        self.blueprint = Architect([AnotherModel, ExampleModel], prefix='/test')
        self.setup()

        resp = self.client.get(f'/test/{FIXED_TABLENAME}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json.get('data'), [])

        resp = self.client.get(f'/test/{SECOND_TABLENAME}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json.get('data'), [{'id': 1, 'label': 'test'}])

    def test_get_one_not_found(self):
        resp = self.client.get(f'/test/{FIXED_TABLENAME}/1')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json, {'error': 'Resource does not exist', 'msg': ''})

    def test_get_one_exists(self):
        self.create()
        resp = self.client.get(f'/test/1')
        # resp = self.client.get(f'/test/{FIXED_TABLENAME}/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, self.second)

    def test_get_one_field_lookup(self):
        self.create()
        resp = self.client.get(f'/test/1/label')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json.get('data'), {'label': 'test'})

    def test_get_one_path_lookup(self):
        self.create()
        resp = self.client.get(f'/test/1/related/label')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json.get('data'), {'label': 'test'})

    def test_get_with_custom_decorator(self):
        def outer(func):
            @wraps(func)
            def decorator(*args, **kwargs):
                if not request.headers.get('API_TOKEN') == 'test':
                    raise HTTPForbidden()
                return func(*args, **kwargs)
            return decorator

        self.blueprint = Architect(ExampleModel, prefix='/test-decorator', decorators=(outer, ))
        self.setup()

        resp = self.client.get(f'/test-decorator')
        # Not truly 404 but decorator interrupts the request and forces an exception
        self.assertEqual(resp.status_code, 403)

        resp = self.client.get(f'/test-decorator', headers={'API_TOKEN': 'test'})
        # Passing the decorator then allows the function to pass through to request as normal
        self.assertEqual(resp.status_code, 200)

    def test_post_endpoint(self):
        payload = dict(label='test')
        resp = self.client.post('/test')
        self.assertEqual(resp.status_code, 422)

        resp = self.client.post('/test', json=payload)
        self.assertEqual(resp.status_code, 201)

        resp = self.client.get(f'/test/{resp.json.get("data").get("id")}')
        self.assertEqual(resp.json, self.expected)

    def test_put_endpoint(self):
        self.create()
        self.create()
        payload = dict(label='new value', related=2)
        resp = self.client.put('/test/1', json=payload)
        self.assertEqual(resp.status_code, 202)

        resp = self.client.get(f'/test/1')
        self.assertEqual(resp.json, {'data': {'id': 1, 'label': 'new value', 'related_id': 2, 'state': 'Y'}})

    def test_delete_endpoint(self):
        self.create()
        resp = self.client.delete('/test/1')
        self.assertEqual(resp.status_code, 200)
