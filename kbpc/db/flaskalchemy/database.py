from datetime import datetime

from flask_sqlalchemy import Model
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.orm import class_mapper

db = SQLAlchemy()


def check_inputs(cls, field, value):
    if isinstance(field, str):
        key_name = field
    else:
        key_name = field.name

    instrument = getattr(cls, field)
    if instrument.key not in cls.__dict__.keys() or key_name is None:
        raise ValueError('Invalid input field')
    instrument_key = instrument.key
    return {instrument_key: value}


class DeclarativeBase(Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, info={'label': 'Primary ID'})
    active = db.Column(db.VARCHAR(2), primary_key=False, nullable=True, info={'label': 'Active'}, default='Y')

    def persist(self):
        db.session.add(self)
        return db.session.commit()

    def delete(self):
        db.session.delete(self)
        return db.session.commit()

    @classmethod
    def purge(cls):
        cls.query.delete()

    @classmethod
    def get(cls, limit=None, order=None):
        if limit:
            return cls.query.limit(limit).all()
        try:
            return cls.query.filter(cls.active != 'D').order_by(order).all()
        except Exception:
            pass

    @classmethod
    def get_schema(cls, exclude=None):
        if exclude is None:
            exclude = []
        schema = []
        for item in [key for key in list(cls.__table__.columns.keys()) if key not in exclude]:
            schema.append(
                dict(name=item.replace('_', ' '), key=item)
            )
        return schema

    @classmethod
    def keys(cls):
        all_keys = set(cls.__table__.columns.keys())
        relations = set(cls.__mapper__.relationships.keys())
        return all_keys - relations

    @classmethod
    def getkey(cls, field):
        return getattr(cls, field).key

    @classmethod
    def get_one_by_field(cls, field, value):
        lookup = check_inputs(cls, field, value)

        return cls.query.filter_by(**lookup).first()

    @classmethod
    def get_all_by_field(cls, field, value, limit=None):
        lookup = check_inputs(cls, field, value)
        return cls.query.filter_by(**lookup).all()

    def columns(self):
        return [prop.key for prop in class_mapper(self.__class__).iterate_properties if
                isinstance(prop, ColumnProperty)]

    def prepare(self, rel=False, json=True, exc=None):
        """
        This utility function dynamically converts Alchemy model classes into a dict using introspective lookups.
        This saves on manually mapping each model and all the fields. However, exclusions should be noted.
        Such as passwords and protected properties.
        :param json: boolean for whether to return JSON or model instance format data
        :param rel: Whether or not to introspect to FK's
        :param exc: Fields to exclude from query result set
        :return: json data structure of model
        :rtype: dict
        """

        if exc is None:
            exc = ['password']
        else:
            exc.append('password')

        if not json:
            return self

        # Define our model properties here. Columns and Schema relationships
        columns = [col for col in self.__mapper__.columns.keys() if col not in exc]
        mapped_relationships = self.__mapper__.relationships.keys()
        model_dictionary = self.__dict__
        resp = {}

        # First lets map the basic model attributes to key value pairs
        for c in columns:
            if isinstance(model_dictionary[c], datetime):
                resp[c] = str(model_dictionary[c])
            else:
                resp[c] = model_dictionary[c]
        if rel is False or not mapped_relationships:
            return resp

        # Now map the relationships
        for r in mapped_relationships:
            try:
                if isinstance(getattr(self, r), list):
                    resp[r] = [
                        i.prepare(rel=False, exc=exc) for i in getattr(self, r)
                    ]
                else:
                    resp[r] = getattr(self, r).prepare(rel=False, exc=exc)

            except Exception as error:
                pass
        return resp

    def __eq__(self, comparison):
        if type(self) != type(comparison):
            raise ValueError('Objects are not the same. Cannot compare')
        base = self.columns()
        base_dictionary = self.__dict__
        comp_dictionary = self.__dict__
        flag = True
        for column_name in base:
            if base_dictionary[column_name] != comp_dictionary[column_name]:
                flag = False
                break
        return flag

    @classmethod
    def create(cls, **payload):
        instance = cls()
        instance.update(commit=False, **payload)
        return instance

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            if attr != 'id':
                setattr(self, attr, value)
        return commit and self.save() or self


def create():
    db.create_all()
