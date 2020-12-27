import unittest
from unittest import mock
from unittest.mock import MagicMock

from flask import Flask
from flask import Response
from flask_sqlalchemy import SQLAlchemy

from flask_atomic.blueprint.core import CoreBlueprint
from flask_atomic.dao.base import BaseDAO
from flask_atomic.dao.buffer.data import DataBuffer
from flask_atomic.orm.base import DeclarativeBase

app = Flask(__name__)
db = SQLAlchemy()


class MockModel(DeclarativeBase):
    id = db.Column(db.String(256), nullable=True, primary_key=True)
    label = db.Column(db.String(256), nullable=True)


class SecondMockModel(DeclarativeBase):
    id = db.Column(db.String(256), nullable=True, primary_key=True)
    label = db.Column(db.String(256), nullable=True)


class TestCore(unittest.TestCase):

    def setUp(self) -> None:
        self.test_model = MockModel(label='test')
        self.instance = CoreBlueprint('blueprint-name', __name__, self.test_model)
        self.client = app
        self.test_client = app.test_client()
        self.client.testing = True

    def tearDown(self) -> None: pass

    def mocked_dao_request_response(self):
        model = SecondMockModel(label='test')
        return DataBuffer(SecondMockModel(label='test'), model.schema())

    def test_init_with_correct_input(self):
        instance = CoreBlueprint('blueprint-name', __name__, self.test_model)
        self.assertIsInstance(instance.dao, type(BaseDAO))

    def test_init_with_invalid_input(self):
        with self.assertRaises(TypeError):
            # Left unfilled on purpose
            CoreBlueprint('blueprint-name', __name__)

    def test_set_dao(self):
        result = self.instance.set_dao(None, MockModel)
        self.assertIsInstance(result, type(BaseDAO))

    @mock.patch('flask_atomic.blueprint.core.CoreBlueprint._CoreBlueprint__dao_query_forwarder')
    def test_default_get_request(self, mocked_call: MagicMock):
        model = SecondMockModel(label='test')
        mocked_call.return_value = DataBuffer([SecondMockModel(label='test')], model.schema())
        with self.client.test_request_context():
            resp = self.instance._CoreBlueprint__default_get_request()
            self.assertEquals(len(resp.json.get('data')), 1)
            self.assertEquals(resp.status_code, 200)

    @mock.patch('flask_atomic.blueprint.core.CoreBlueprint._CoreBlueprint__dao_query_forwarder')
    def test_default_get_field_request(self, mocked_call: MagicMock):
        mocked_call.return_value = self.mocked_dao_request_response()
        with self.client.test_request_context():
            resp: Response = self.instance._CoreBlueprint__default_get_field_request(1, 'label')
            self.assertEquals(resp.json.get('label'), 'test')
            self.assertEquals(resp.status_code, 200)
