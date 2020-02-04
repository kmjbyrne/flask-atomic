from collections import Iterable
from datetime import datetime
from typing import Optional

from sqlalchemy.orm.attributes import InstrumentedAttribute

from flask_atomic.logger import get_logger
from flask_atomic.orm.database import db
from flask_atomic.orm.mixins.core import CoreMixin

logger = get_logger(__name__)


class DeclarativeBase(db.Model, CoreMixin):
    """
    Base model to be extended for use with Flask projects.

    Core concept of the model is common functions to help wrap up database
    interaction into a single interface. Testing can be rolled up easier this
    way also. Inheriting from this class automatically sets id field and db
    soft deletion field managed by active using the DYNA pattern (D, Y, N, A).

    Basic usage::

        from flask_atomic.sqlalchemy.declarative import DeclarativeBase

        class MyNewModel(DeclarativeBase):
            field_a = db.Column(db.String(256), nullable=True)

    """

    __abstract__ = True

    @classmethod
    def identify_primary_key(cls):
        return list(cls.__table__.primary_key).pop().name

    @classmethod
    def checkfilters(cls, filters):
        resp = {}
        for k, v in filters.items():
            resp[cls.normalise(k)] = v
        return resp

    @classmethod
    def makequery(cls):
        try:
            return cls.query
        except Exception as e:
            logger.error(str(e))
            db.session.rollback()
        return cls.query

    @classmethod
    def keys(cls, rel=True):
        all_keys = set(cls.__table__.columns.keys())
        relations = set(cls.__mapper__.relationships.keys())

        if not rel:
            return all_keys.difference(relations)
        return all_keys.union(relations)

    @classmethod
    def schema(cls, rel=True, exclude=None):
        if exclude is None:
            exclude = []
        schema = []
        for item in [key for key in cls.keys(rel=rel) if key not in exclude]:
            schema.append(dict(name=item.replace('_', ' '), key=item))
        return schema

    @classmethod
    def getkey(cls, field):
        if isinstance(field, InstrumentedAttribute):
            return getattr(cls, field.key)
        return getattr(cls, field)

    def relationships(self, root=''):
        return list(filter(lambda r: r != root, self.__mapper__.relationships.keys()))

    def columns(self, exc: Optional[list]) -> list:
        """
        Gets a list of columns to work with, minus the excluded sublist (exc).

        :param exc:
        :return:
        """

        if exc is None:
            exc = list()
        return [key for key in list(self.__table__.columns.keys()) if key not in exc]

    def whatami(self) -> str:
        """
        Self-describe the model.

        :return: Descriptive name based on the tablename used at declaration.
        """

        # I am not a number :)
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
                        resp[item][index][grandchild] = getattr(entry, grandchild).extract_data()
            elif relationship_instance:
                resp[item] = relationship_instance.extract_data(exc)
        return resp

    def extract_data(self, exc: Optional[list]) -> dict:
        resp = dict()
        if exc is None:
            exc = Iterable()
        for column in self.columns(exc):
            if isinstance(getattr(self, column), datetime):
                resp[column] = str(getattr(self, column))
            else:
                resp[column] = getattr(self, column)
        return resp

    def serialize(self, exc: Optional[list], rel=True, root=None):
        """
        This utility function dynamically converts Alchemy model classes into a
        dict using introspective lookups. This saves on manually mapping each
        model and all the fields. However, exclusions should be noted. Such as
        passwords and protected properties.

        :param rel: Whether or not to introspect to relationships
        :param exc: Fields to exclude from query result set
        :param root: Root model for processing relationships. This acts as a
        recursive sentinel to prevent infinite recursion due to selecting oneself
        as a related model, and then infinitely trying to traverse the roots
        own relationships, from itself over and over.

        Only remedy to this is also to use one way relationships. Avoiding any
        back referencing of models.

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
