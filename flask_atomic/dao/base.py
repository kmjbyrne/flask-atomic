import copy
from datetime import datetime
from typing import Optional

import sqlalchemy

from flask import current_app
from flask import request

from flask_atomic.dao.buffer.data import DataBuffer
from flask_atomic.dao.buffer.query import QueryBuffer
from flask_atomic.dao.querystring import QueryStringProcessor
from flask_atomic.httputils.exceptions import HTTPConflict


class BaseDAO:

    def __init__(self, model=None, *args, **kwargs):
        self.json = True
        self.exclusions = list()
        self.rels: bool = False
        self.sortkey: None = getattr(model, model.identify_primary_key())
        self.descending: bool = False
        # TODO Break out this code to a class and encapsulate mapping a little better
        self.filters = {}
        self._schema = None
        self.model = model
        self.queryargs = None
        self.__provided = kwargs.get('querystring', None)
        self.queryargs: Optional[QueryStringProcessor] = QueryStringProcessor(kwargs.get('querystring', None))
        self.auto = False
        if self.__provided:
            self.auto = True

    def autoquery(self):
        if not self.__provided:
            self.queryargs = QueryStringProcessor(request.args)
            self.auto = True
        return self

    def i(self):
        return self.model

    @property
    def iquery(self):
        query = self.create_query()
        self._schema = query.column_descriptions
        return QueryBuffer(query, self.model).query

    def schema(self, exclude=None):
        schema = {
            'model': self._schema[0].get('name'),
            'fields': []
        }

        for item in self._schema[1:]:
            schema['fields'].append(
                dict(name=item.get('name'), type=str(item.get('type')), expr=str(item.get('expr')))
            )
        return schema

    def __iskey(self, val):
        return val in self.model.keys()

    def columns(self, exclusions):
        if not exclusions:
            exclusions = set()
        includes = []
        for item in self.model.objectcolumns(False):
            comp = item
            if not isinstance(comp, str):
                comp = item.key
            if comp not in exclusions:
                includes.append(item)
        return includes

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

    def relationattrs(self, relations):
        included_relationships = tuple()
        if relations and not isinstance(relations, list):
            for item in self.model.relationattrs():
                included_relationships = included_relationships + (getattr(self.model, item),)
            return included_relationships
        elif isinstance(relations, list):
            for item in relations:
                included_relationships.append(getattr(self.model, item))
            return included_relationships
        return None

    def create_query(self, fields=None, flagged=False):
        return self.model.makequery(fields)

    def query(self, noauto=False):
        query = self.create_query()
        buffer = QueryBuffer(query, self.model, queryargs=self.queryargs)
        if noauto:
            return buffer
        buffer.autoquery()
        return buffer

    def delete(self, instanceid):
        instance = self.get_one(instanceid).view()
        clone = copy.deepcopy(instance)
        try:
            instance.delete()
        except AttributeError:
            raise AttributeError('This resource does not exist or may have already been deleted')
        return clone

    def get(self, flagged=False):
        return self._get()
        # query = self.create_query(self.columns(self.queryargs.exclusions))
        # self._schema = query.column_descriptions
        # buffer = QueryBuffer(query, self.model, vflag=flagged, queryargs=self.queryargs)
        # buffer.order_by(self.queryargs.sortkey or self.sortkey, descending=self.queryargs.descending)
        # buffer.filter([self.queryargs.min])
        # buffer.filter_by(self.queryargs.filters)
        # # buffer.includerels(self.relationattrs(self.queryargs.rels))
        #
        # try:
        #     return buffer.limit(self.queryargs.limit).all()
        # except AttributeError as error:
        #     raise Exception(str(error))

    def _get(self, flagged=False):
        query = self.create_query(self.columns(self.queryargs.exclusions))
        self._schema = query.column_descriptions
        # includes
        # excludes
        # relationships
        buffer = QueryBuffer(query, self.model, queryargs=self.queryargs)
        return buffer.all()
        # try:
        #     return buffer.limit(self.queryargs.limit).all()
        # except AttributeError as error:
        #     raise Exception(str(error))

    def get_one(self, value, flagged=False):
        self.filters.update({self.model.id: value})
        query = self.create_query(self.columns(self.queryargs.exclusions))
        self._schema = query.column_descriptions
        buffer = QueryBuffer(query, self.model, vflag=flagged, queryargs=self.queryargs)
        return buffer.filter_by(self.filters).first()

    def get_all_by(self, field, value, flagged=False):
        pkfilter = {field: value}
        query = self.create_query(self.columns(self.queryargs.exclusions))
        self._schema = query.column_descriptions
        buffer = QueryBuffer(query, self.model, vflag=flagged, queryargs=self.queryargs)
        return buffer.filter_by(pkfilter).all()

    def get_one_by(self, field, value, flagged=False):
        pkfilter = {field: value}
        query = self.create_query(self.columns(self.queryargs.exclusions))
        self._schema = query.column_descriptions
        buffer = QueryBuffer(query, self.model, vflag=flagged, queryargs=self.queryargs)
        return buffer.filter_by(pkfilter).first()

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
        instance = self.model(**payload)
        return DataBuffer(self.save(instance), instance.schema(), instance.fields(), False)

    def save(self, instance):
        try:
            instance.save(commit=True)
            return instance
        except sqlalchemy.exc.IntegrityError as error:
            current_app.logger.error(str(error))
            raise HTTPConflict(f'{str(instance).capitalize()} with part or all of these details already exists')

    def update(self, instance_id, payload):
        instance = self.get_one(instance_id).view()

        if 'last_update' in instance.fields():
            payload.update(last_update=datetime.now())

        instance.update(**payload)
        instance.save()
        return instance

    def iupdate(self, instance, instance_id, payload):
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
            raise ValueError('This entry does not exist or maybe has been marked for deletion.')
        instance.active = 'D'
        instance.save()
        return instance
