import copy
from datetime import datetime
from typing import Optional
from typing import Type

import sqlalchemy

from flask_atomic.dao.buffer.data import DataBuffer
from flask_atomic.dao.buffer.query import QueryBuffer
from flask_atomic.dao.querystring import QueryStringProcessor
from flask_atomic.httputils.exceptions import HTTPException
from flask_atomic.orm.declaratives.base import DeclarativeBase


class QueryArgs:
    reverse = False


class BaseDAO:
    json = True
    model: Type[DeclarativeBase]
    exclusions = list()
    rels: bool = True
    sortkey: str = None
    descending: bool = False
    queryargs: Optional[QueryStringProcessor]
    # TODO Break out this code to a class and encapsulate mapping a little better
    querystring = None
    filters = {}

    def __init__(self, model=None, *args, **kwargs):
        self.model = model
        if kwargs.get('querystring'):
            self.queryargs = QueryStringProcessor(kwargs.get('querystring'))

    def schema(self, exclude=None):
        if not exclude:
            exclude = []
        return self.model.schema(exclude=self.exclusions + exclude, rel=self.rels)

    def __iskey(self, val):
        return val in self.model.keys()

    @classmethod
    def model_schema(cls, exclude=None):
        return cls.model.schema(exclude=exclude)

    def validate_arguments(self, payload):
        valid_fields = dir(self.model)
        valid = True
        invalid_fields = []

        for item in payload:
            if item not in valid_fields:
                invalid_fields.append(item)
                valid = False

        if valid is False:
            raise ValueError(
                '<{}> not accepted as input field(s)'.format(', '.join(invalid_fields)))
        return True

    def create_query(self, flagged=False):
        return self.model.makequery()
        # return QueryBuffer(query, self.model, vflag=flagged, rel=self.rels, dao=self)

    def delete(self, instanceid):
        instance = self.get_one(instanceid).view()
        clone = copy.deepcopy(instance)
        instance.delete()
        return clone

    def query(self):
        query = self.create_query()
        buffer = QueryBuffer(query, self.model)
        return buffer

    def get(self, flagged=False):
        query = self.create_query()
        buffer = QueryBuffer(query, self.model, vflag=flagged)
        buffer.order_by(self.sortkey, self.descending)
        return buffer.filter(self.filters).all()

    def get_one(self, value, flagged=False):
        self.filters.update({self.model.id: value})
        query = self.model.makequery()
        buffer = QueryBuffer(query, self.model, vflag=flagged)
        return buffer.filter(self.filters).first()

    def get_all_by(self, field, value, flagged=False):
        pkfilter = {field: value}
        query = self.model.makequery()
        buffer = QueryBuffer(query, self.model, vflag=flagged)
        return buffer.filter(pkfilter).all()

    def get_one_by(self, field, value, flagged=False):
        pkfilter = {field: value}
        query = self.model.makequery()
        buffer = QueryBuffer(query, self.model, vflag=flagged)
        return buffer.filter(pkfilter).first()

    def remove_association(self, rootid, associated_id, relationship):
        base = self.get_one(rootid).view()
        association = None
        for item in getattr(base, relationship):
            if str(item.id) == associated_id:
                association = item

        if association is not None:
            getattr(base, relationship).remove(association)
            base.save()
        return base

    def create(self, payload):
        self.validate_arguments(payload)
        instance = self.model.create(**payload)
        return DataBuffer(self.save(instance), instance.schema())

    def save(self, instance):
        try:
            instance.save(commit=True)
            return instance
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException('Entity with part or all of these details already exists', code=409)

    def update(self, instance_id, payload):
        instance = self.get_one(instance_id).view()

        if 'last_update' in instance.fields():
            payload.update(last_update=datetime.now())

        instance.update(**payload)
        instance.save()
        return instance

    def sdelete(self, instance_id):
        """
        Soft delete instruction. Does not remove data. Useful for not related resources.

        :param instance_id: Primary key for the resource to be deleted
        :return: instance copy with new D flag
        """

        instance = self.get_one(instance_id, flagged=True).view()
        if instance is None or instance.active == 'D':
            raise ValueError('This entry does not exist or maybe have been marked for deletion.')
        instance.active = 'D'
        instance.save()
        return instance
