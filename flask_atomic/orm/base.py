from datetime import datetime
from datetime import date
from typing import Optional

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import dynamic
from flask_atomic.orm.database import db
from flask_atomic.orm.mixins.core import CoreMixin


def extract(model, fields=None, exclude: Optional[set] = None) -> dict:
    resp = dict()
    if exclude is None:
        exclude = set()

    if fields is None:
        fields = model.keys()

    restricted_fields = getattr(model, 'RESTRICTED_FIELDS', set())
    if restricted_fields:
        fields.discard(restricted_fields)
        exclude = exclude.union(restricted_fields or set())

    for column in set(fields).difference(set(exclude)):
        if isinstance(getattr(model, column), datetime) or isinstance(getattr(model, column), date):
            resp[column] = str(getattr(model, column))
        else:
            resp[column] = getattr(model, column)
    return resp


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
    # active = db.Column(db.String(5), default='Y')

    def __hash__(self):
        return self.id

    def __str__(self):
        return self.whatami()

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
    def getquery(cls):
        return db.session.query

    @classmethod
    def makequery(cls, fields=None):
        try:
            # return db.session.query(cls, fields)
            if not fields:
                return cls.query
            return db.session.query(cls, *fields)
        except Exception as e:
            db.session.rollback()
        return db.session.query(cls, *fields)

    @classmethod
    def relations(cls, flag):
        if flag == True:
            return set(cls.__mapper__.relationships.keys())
        elif isinstance(flag, list):
            return set(flag)
        return set()

    @classmethod
    def relationattrs(cls):
        return set(cls.__mapper__.relationships.keys())

    @classmethod
    def objectcolumns(cls, include_relationships=False):
        bound_columns = set(cls.__mapper__.columns)
        if include_relationships:
            rels = cls.__mapper__.relationships
            return bound_columns.union(set([i.class_attribute for i in cls.__mapper__.relationships]))
        return bound_columns

    @classmethod
    def keys(cls):
        return set(cls.__table__.columns.keys())

    @classmethod
    def schema(cls, rel=True, exclude=None):
        if exclude is None:
            exclude = []
        schema = []
        for item in [key for key in cls.keys() if key not in exclude]:
            schema.append(dict(name=item.replace('_', ' '), key=item))
        return schema

    @classmethod
    def getkey(cls, field):
        if isinstance(field, InstrumentedAttribute):
            return getattr(cls, field.key)
        return getattr(cls, field)

    def relationships(self, root=''):
        return list(filter(lambda r: r != root, self.__mapper__.relationships.keys()))

    def columns(self, exc: Optional[list] = None) -> list:
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

    def process_relationships(self, root: str, exclude: set = None, rels=None):
        resp = dict()

        if rels is None or isinstance(rels, bool):
            rels = self.relationships(root)

        for idx, item in enumerate(rels):
            # First check if it is a sub lookup
            _lookup = None
            if hasattr(self, '__i__' + item):
                resp[item] = getattr(self, '__i__' + item)
                continue

            sublookup = False
            if '.' in item:
                sublookup = True
                lookup = item.split('.')
                _lookup = lookup.copy()
                relationship_instance = getattr(getattr(self, lookup.pop(0), None), lookup.pop())
            else:
                relationship_instance = getattr(self, item, None)

            if isinstance(relationship_instance, dynamic.AppenderMixin):
                # TO handle dynamic relationships (lazy=dynamic)
                fields = set(map(lambda x: x.key, relationship_instance._entity_zero().column_attrs)).difference(exclude)
                resp[item] = []
                if hasattr(self, '__i__' + item):
                    resp[item] = getattr(self, '__i__' + item)
                else:
                    for index, entry in enumerate(relationship_instance.all()):
                        resp[item].append(extract(entry, fields))
            elif isinstance(relationship_instance, list):
                # if relationship_instance.uselist:
                if sublookup:
                    parent = _lookup.pop(0)
                    attr = _lookup.pop()
                else:
                    resp[item] = []
                for index, entry in enumerate(relationship_instance):
                    fields = set(entry.keys()).difference(exclude)
                    if sublookup:
                        if not resp.get(parent, None):
                            resp[parent] = dict()
                        resp[parent].setdefault(attr, []).append(entry.extract(fields))
                    else:
                        resp[item].append(entry.extract(set(entry.keys()).difference(exclude)))
            elif relationship_instance:
                fields = set(relationship_instance.keys()).difference(exclude)
                if _lookup:
                    resp[_lookup.pop(0)][_lookup.pop()] = relationship_instance.extract(fields)
                else:
                    resp[item] = relationship_instance.extract(fields)
        return resp

    def extract(self, fields=None, exclude: Optional[set] = None, **kwargs) -> dict:
        resp = dict()
        if exclude is None:
            exclude = set()

        if fields is None:
            fields = self.keys()

        restricted_fields = getattr(self, 'RESTRICTED_FIELDS', set())
        if restricted_fields and not kwargs.get('private', None):
            fields.discard(restricted_fields)
            exclude = exclude.union(restricted_fields or set())

        for column in set(fields).difference(set(exclude)):
            if isinstance(getattr(self, column), datetime) or isinstance(getattr(self, column), date):
                resp[column] = str(getattr(self, column))
            else:
                resp[column] = getattr(self, column)
        return resp

    def serialize(self, fields=None, exc: Optional[set] = None, rels=False, root=None, exclude=None, functions=None,
                  **kwargs):
        """
        This utility function dynamically converts Alchemy model classes into a
        dict using introspective lookups. This saves on manually mapping each
        model and all the fields. However, exclusions should be noted. Such as
        passwords and protected properties.

        :param functions:
        :param fields: More of a whitelist of fields to include (preferred way)
        :param rels: Whether or not to introspect to relationships
        :param exc: Fields to exclude from query result set
        :param root: Root model for processing relationships. This acts as a
        recursive sentinel to prevent infinite recursion due to selecting oneself
        as a related model, and then infinitely trying to traverse the roots
        own relationships, from itself over and over.
        :param exclude: Exclusion in set form. Currently in favour of exc param.

        Only remedy to this is also to use one way relationships. Avoiding any
        back referencing of models.

        :return: json data structure of model
        :rtype: dict
        """

        if functions is None:
            functions = {}
        if exclude is None:
            exclude = set()
        else:
            exclude = set(exclude)
        if not fields:
            fields = set(self.fields())

        if root is None:
            root = self.whatami()

        if exc is None:
            exc = {'password'}

        set(exclude).union(exc)
        # Define our model properties here. Columns and Schema relationships
        resp = self.extract(fields, exc, **kwargs)

        if functions:
            for key, value in functions.items():
                resp[f'_{key}'] = value(getattr(self, key))

        restricted_fields = set(fields).discard(getattr(self, 'RESTRICTED_FIELDS', set()))
        if restricted_fields:
            fields.discard(restricted_fields)
            exclude = exclude.union(restricted_fields or set())

        rels = rels or set(self.relationships()).intersection(fields)
        if not rels or len(set(self.relationships())) < 1:
            return resp

        # for rel in rels:
        #     if rel in [i.split('__i__').pop() for i in self.__dict__ if '__i__' in i]:
        #         rels.remove(rel)

        resp.update(self.process_relationships(root, rels=rels, exclude=exclude))
        return resp