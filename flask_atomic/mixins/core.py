from flask import current_app
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import InstrumentedAttribute

from sqlalchemy_blender.helpers import iserialize
from flask_atomic.database import db
# from flask_atomic.orm.database import db
from flask_atomic.orm.operators import commitsession


def session():
    db = current_app.extensions.get('sqlalchemy', None).db
    if not db:
        raise RuntimeError('A DB instance is required')
    return db.session


class JSONMixin:

    def json(self):
        return iserialize(self)


class CoreMixin(object):
    __abstract__ = True


    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    @classmethod
    def normalise(cls, field):
        """
        Checks whether filter or field key is an InstumentedAttribute and returns
        a usable string instead. InstrumentedAttributes are not compatible with
        queries. Therefore, they must be transformed to correct types.

        :param field: The field we need to check
        :return: Transformed field
        """

        if isinstance(field, InstrumentedAttribute):
            return field.name
        return field

    @classmethod
    def fields(cls, inc=None, exc=None):
        if inc is None:
            inc = []
        if exc is None:
            exc = []

        normalised_fields = []
        for field in list(key for key in cls.keys() if
                          key not in [cls.normalise(e) for e in exc]):
            normalised_fields.append(cls.normalise(field))
        return normalised_fields

    @classmethod
    def create(cls, **payload):
        instance = cls()
        return instance.update(commit=True, **payload)

    def delete(self):
        x = current_app
        session().delete(self)
        commitsession()

    def save(self, commit=True):
        session().add(self)
        x = current_app
        if commit:
            commitsession()
        return self

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            if attr != 'id' and attr in self.fields():
                setattr(self, attr, value)

        for mtm in set(self.relationattrs()).intersection(set(kwargs.keys())):
            model = getattr(self, mtm)
            current = set(map(lambda rel: getattr(rel, rel.identify_primary_key()), model))
            candidates = set(map(lambda item: list(item.values()).pop(), kwargs[mtm]))
            for addition in candidates.difference(current):
                association = session().query(self.__mapper__.relationships.classgroups.entity).get(addition)
                getattr(self, mtm).append(association)

            for removal in current.difference(candidates):
                association = session().query(self.__mapper__.relationships.classgroups.entity).get(removal)
                getattr(self, mtm).remove(association)
        self.save()
        return self

    def commit(self):
        return commitsession()
