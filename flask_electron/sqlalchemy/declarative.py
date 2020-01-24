from collections import Iterable
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.attributes import InstrumentedAttribute

from flask_electron.logger import get_logger

db = SQLAlchemy()

logger = get_logger(__name__)


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


def sessioncommit():
    try:
        db.session.commit()
        # db.session.close()
        return
    except OperationalError as operror:
        logger.info(str(operror))
        db.session.rollback()
        db.session.close()
        db.session.close()
    except IntegrityError as integerror:
        raise integerror
    except Exception as error:
        raise Exception
    finally:
        logger.info(str('DB execution cycle complete'))


class DeclarativeBase(db.Model):
    """
    Base model to be extended for use with Flask projects.

    Core concept of the model is common functions to help wrap up database
    interaction into a single interface. Testing can be rolled up easier this
    way also. Inheriting from this class automatically sets id field and db
    soft deletion field managed by active using the DYNA pattern (D, Y, N, A).

    Basic usage::

        from flask_electron.db.flaskalchemy.database import DeclarativeBase

        class MyNewModel(DeclarativeBase):
            field_a = db.Column(db.String(256), nullable=True)

    """

    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    active = db.Column(db.VARCHAR(2), primary_key=False, default='Y')

    @classmethod
    def normalise(cls, field):
        """
        Checks whether filter or field key is an InstumentedAttribute and returns a usable string instead.
        InstrumentedAttributes are not compatible with queries.

        :param field:
        :return:
        """

        if isinstance(field, InstrumentedAttribute):
            return field.name
        return field

    @classmethod
    def checkfilters(cls, filters):
        resp = {}
        for k, v in filters.items():
            resp[cls.normalise(k)] = v
        return resp

    @classmethod
    def fields(cls, inc=None, exc=None):
        if inc is None:
            inc = []
        if exc is None:
            exc = []

        normalised_fields = []
        for field in list(key for key in cls.keys() if key not in [cls.normalise(e) for e in exc]):
            normalised_fields.append(cls.normalise(field))
        return normalised_fields

    @classmethod
    def makequery(cls):
        try:
            return cls.query
        except Exception as e:
            logger.error(str(e))
            db.session.rollback()
        return cls.query

    @classmethod
    def schema(cls, rel=True, exclude=None):
        if exclude is None:
            exclude = []
        schema = []
        for item in [key for key in cls.keys(rel=rel) if key not in exclude]:
            schema.append(dict(name=item.replace('_', ' '), key=item))
        return schema

    @classmethod
    def keys(cls, rel=True):
        all_keys = set(cls.__table__.columns.keys())
        relations = set(cls.__mapper__.relationships.keys())

        if not rel:
            return all_keys.difference(relations)
        return all_keys.union(relations)

    @classmethod
    def getkey(cls, field):
        if isinstance(field, InstrumentedAttribute):
            return getattr(cls, field.key)
        return getattr(cls, field)

    def relationships(self, root=''):
        return list(filter(lambda r: r != root, self.__mapper__.relationships.keys()))

    def columns(self, exc):
        return [key for key in list(self.__table__.columns.keys()) if key not in exc]

    def whatami(self):
        return self.__tablename__

    def process_relationships(self, root: str, exc: list = None):
        resp = dict()
        for item in self.relationships(root):
            relationship_instance = getattr(self, item)
            if isinstance(relationship_instance, list):
                resp[item] = [i.extract_data(exc) for i in relationship_instance]
                for index, entry in enumerate(relationship_instance):
                    for grandchild in entry.relationships(root):
                        print(grandchild)
                        resp[item][index][grandchild] = getattr(entry, grandchild).extract_data(())
            elif relationship_instance:
                resp[item] = relationship_instance.extract_data(exc)
        return resp

    def extract_data(self, exc: Iterable = None) -> dict:
        resp = dict()
        if exc is None:
            exc = Iterable()
        for column in self.columns(exc):
            if isinstance(getattr(self, column), datetime):
                resp[column] = str(getattr(self, column))
            else:
                resp[column] = getattr(self, column)
        return resp

    def prepare(self, rel=True, exc=None, root=None):
        """
        This utility function dynamically converts Alchemy model classes into a dict using introspective lookups.
        This saves on manually mapping each model and all the fields. However, exclusions should be noted.
        Such as passwords and protected properties.

        :param rel: Whether or not to introspect to FK's
        :param exc: Fields to exclude from query result set
        :param root: Root model for processing relationships

        :return: json data structure of model
        :rtype: dict
        """

        if root is None:
            root = self.whatami()

        if exc is None:
            exc = ['password']
        else:
            exc.append('password')

        # Define our model properties here. Columns and Schema relationships
        resp = self.extract_data(exc)
        if not rel:
            return resp

        resp.update(self.process_relationships(root, exc=exc))
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
        return instance.update(commit=True, **payload)

    def delete(self):
        db.session.delete(self)
        sessioncommit()

    def sdelete(self, _commit=True):
        self.active = 'D'
        sessioncommit()
        return _commit and self.save() or self

    def restore(self, _commit=True):
        self.active = 'Y'
        sessioncommit()
        return _commit and self.save() or self

    def save(self, _commit=True):
        db.session.add(self)
        if _commit:
            sessioncommit()
        db.session.refresh(self)
        return self

    def update(self, _commit=True, **kwargs):
        for attr, value in kwargs.items():
            if attr != 'id' and attr in self.fields():
                setattr(self, attr, value)
        # return _commit and self.save() or self
        return self

    def commit(self):
        return sessioncommit()

    @classmethod
    def purge(cls):
        cls.query.delete()
        return sessioncommit()

    def close(self):
        db.session.close()


def create():
    db.create_all()
