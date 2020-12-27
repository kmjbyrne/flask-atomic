import unittest

from flask import Flask
from flask import request
from flask import current_app
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from handyhttp import HTTPSuccess
from handyhttp.exceptions import HTTPNotFound
from handyhttp.exceptions import HTTPForbidden

from flask_atomic import Architect
# from flask_atomic.helpers import db

db = SQLAlchemy()

FIXED_TABLENAME = 'example'
SECOND_TABLENAME = 'second'


class ExampleModel(db.Model):
    __tablename__ = FIXED_TABLENAME
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(256), nullable=True)
    related = db.relationship('AnotherModel', cascade='all, delete', backref=db.backref('examples', lazy=True))
    related_id = db.Column(db.Integer, db.ForeignKey(f'{SECOND_TABLENAME}.id'), nullable=True)


class AnotherModel(db.Model):
    __tablename__ = SECOND_TABLENAME
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(256), nullable=True)


class BaseAppTest(unittest.TestCase):
    def setUp(self) -> None:
        self.flask = Flask(__name__)
        db.init_app(self.flask)

        self.blueprint = Architect(ExampleModel, prefix='/test')
        self.blueprint.link(self.flask)
        self.client = self.flask.test_client()

        with self.flask.app_context():
            db.create_all()
            entity = AnotherModel(label='test')
            db.session.add(entity)
            db.session.commit()

    def setup(self):
        self.blueprint.link(self.flask)
        self.client = self.flask.test_client()

        with self.flask.app_context():
            db.create_all()


class TestBlueprintFunctionality(BaseAppTest):
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
        self.assertEqual(resp.json, {'error': 'Resource does not exist', 'msg': 'Example not found!'})

    def test_get_one_exists(self):
        with self.flask.app_context():
            entity = ExampleModel(label='test')
            entity.related_id = 1
            db.session.add(entity)

            other = AnotherModel(label='test')
            db.session.add(other)
            db.session.commit()

        resp = self.client.get(f'/test/1')
        # resp = self.client.get(f'/test/{FIXED_TABLENAME}/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json.get('data'), {'id': 1, 'label': 'test', 'related_id': 1})

    def test_get_one_field_lookup(self):
        with self.flask.app_context():
            entity = ExampleModel(label='test')
            db.session.add(entity)
            db.session.commit()
        resp = self.client.get(f'/test/1/label')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json.get('data'), {'label': 'test'})

    def test_get_one_path_lookup(self):
        with self.flask.app_context():
            entity = ExampleModel(label='test')
            entity.related_id = 1
            db.session.add(entity)
            db.session.commit()
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
