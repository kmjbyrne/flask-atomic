import unittest
import threading
import urllib

from datetime import datetime

from sqlalchemy_blender.helpers import json
from flask_atomic.ext import FlaskJSON
from flask_atomic.ext import ModelEncoder
from flask_atomic.ext import JSONResponse
from handyhttp import HTTPSuccess

from tests.fixtures.fixtures import db
from tests.fixtures.fixtures import ExampleModel


class TestExtensions(unittest.TestCase):

    def setUp(self) -> None:
        self.app = FlaskJSON(__name__)

        with self.app.app_context():
            db.init_app(self.app)
            db.create_all()
            db.session.add(ExampleModel(label='test'))
            db.session.commit()

        @self.app.route('/', methods=['GET'])
        def index():
            return HTTPSuccess(json(db.session.query(ExampleModel).all()))

        @self.app.route('/date', methods=['GET'])
        def date():
            return datetime.now()

    def test_json_response(self):
        client = self.app.test_client()
        time = datetime.now()

        with self.app.app_context():
            resp = JSONResponse.force_type(time, client.environ_base)
            self.assertEqual(resp.json, time.isoformat())

            resp = JSONResponse.force_type((('test', ), 200), client.environ_base)
            self.assertEqual(resp.json, ['test'])

            resp = JSONResponse.force_type(({'test': 'test'}, 200), client.environ_base)
            self.assertEqual(resp.json, {'test': 'test'})

    def test_model_encoder(self):
        encoder = ModelEncoder()
        with self.app.app_context():
            data = encoder.default(db.session.query(ExampleModel).all())
            self.assertEqual(data, [{'id': 1, 'related_id': None, 'label': 'test', 'state': 'Y'}])

    def test_flask_json_subclass(self):
        client = self.app.test_client()
        client.json_encoder = ModelEncoder

        resp = client.get('/')
        self.assertEqual(resp.status_code, 200)
