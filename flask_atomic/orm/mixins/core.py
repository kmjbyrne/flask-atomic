from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import InstrumentedAttribute

from flask_atomic.orm.database import db
from flask_atomic.orm.operators import commitsession


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

    def unsafe_delete(self):
        db.session.delete(self)
        commitsession()

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            commitsession()
        return self

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            if attr != 'id' and attr in self.fields():
                setattr(self, attr, value)
        self.save()
        return self

    def commit(self):
        return commitsession()
