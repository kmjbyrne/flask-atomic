import unittest
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from kbpc.db.flaskalchemy import serializer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
db = SQLAlchemy(app)


class TestRelationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    model_link_id = db.Column(db.Integer, db.ForeignKey('test_model.id'), nullable=False)
    model_link = db.relationship('TestModel', backref=db.backref('TestRelationship', lazy=True))


class TestModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    age = db.Column(db.Integer)
    dob = db.Column(db.DateTime)


class NestedKeyObj:
    @staticmethod
    def keys():
        return ['field', 'name']


class NestedRelationshipObj:
    @staticmethod
    def keys():
        return ['field', 'name']


class MockColumnsObj:
    columns = NestedKeyObj
    relationships = NestedRelationshipObj


class MockAlchemyObj:
    __mapper__ = MockColumnsObj

    def __init__(self, field, name):
        self.field = field
        self.name = name


class TestTransform(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now()
        db.create_all()
        self.fixture = MockAlchemyObj('test', 'John Doe')
        self.fixed_instance = TestModel(name='John Doe', age=20, dob=self.now)
        self.fixed_relationship_instance = TestRelationship(name='John Doe', model_link_id=1)
        db.session.add(self.fixed_instance)
        db.session.add(self.fixed_relationship_instance)
        db.session.commit()

    def tearDown(self) -> None:
        pass

    def test_get_relationship_keys(self):
        response = serializer.get_relationship_keys(self.fixed_instance)
        expected = ['TestRelationship']
        self.assertEqual(expected, response)

    def test_convert(self):
        response = serializer.convert(self.fixed_instance)
        expected = dict(id=self.fixed_instance.id, name='John Doe', age=20, dob=self.now)
        response_item = dict(
            id=response.get('id'),
            name=response.get('name'),
            age=response.get('age'),
            dob=response.get('dob')
        )
        self.assertEqual(response_item, expected)

    def test_merge_column_sets(self):
        base_set = {1, 2, 3, 4, 5}
        difference_set = {3, 4}
        response = serializer.merge_column_sets(base_set, difference_set)
        expected = {1, 2, 5}
        self.assertEqual(response, expected)

    def test_unpack(self):
        response = serializer.serialize(self.fixed_instance)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get('id'), self.fixed_instance.id)
        self.assertEqual(response.get('name'), self.fixed_instance.name)
        self.assertEqual(response.get('age'), self.fixed_instance.age)
        self.assertEqual(response.get('dob'), self.fixed_instance.dob)

    def test_unpack_with_relationship(self):
        response = serializer.serialize(self.fixed_relationship_instance, include_relationship=True)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get('id'), self.fixed_relationship_instance.id)
        self.assertEqual(response.get('name'), self.fixed_relationship_instance.name)

        self.assertIsInstance(response.get('model_link'), dict)
        self.assertEqual(response.get('model_link').get('id'), self.fixed_relationship_instance.model_link.id)
        self.assertEqual(response.get('model_link').get('name'), self.fixed_relationship_instance.model_link.name)
        self.assertEqual(response.get('model_link').get('age'), self.fixed_relationship_instance.model_link.age)
        self.assertEqual(response.get('model_link').get('dob'), self.fixed_relationship_instance.model_link.dob)

    def test_unpack_with_relationship_and_exclusions(self):
        exclusions = {
            'test_relationship': ['id'],
            'test_model': ['id']
        }
        response = serializer.serialize(self.fixed_relationship_instance, exclusions, include_relationship=True)

        self.assertIsInstance(response, dict)
        self.assertNotIn(self.fixed_relationship_instance.id, response.keys())
        self.assertEqual(response.get('name'), self.fixed_relationship_instance.name)

        self.assertIsInstance(response.get('model_link'), dict)
        self.assertNotIn(self.fixed_relationship_instance.model_link_id, response.get('model_link').keys())
        self.assertEqual(response.get('model_link').get('name'), self.fixed_relationship_instance.model_link.name)
        self.assertEqual(response.get('model_link').get('age'), self.fixed_relationship_instance.model_link.age)
        self.assertEqual(response.get('model_link').get('dob'), self.fixed_relationship_instance.model_link.dob)

    def test_unpack_with_exclusions(self):
        response = serializer.unpack(self.fixed_instance, {'test_model': ['id']})

        self.assertIsInstance(response, dict)
        self.assertNotIn(self.fixed_instance.id, response.keys())
        self.assertEqual(response.get('name'), self.fixed_instance.name)
        self.assertEqual(response.get('age'), self.fixed_instance.age)
        self.assertEqual(response.get('dob'), self.fixed_instance.dob)
