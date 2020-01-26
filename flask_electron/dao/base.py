import copy
from datetime import datetime

import sqlalchemy

from flask_electron.dao.actions import ActionsModel
from flask_electron.dao.data import DataBuffer
from flask_electron.dao.query import QueryBuffer
from flask_electron.http.exceptions import HTTPException


class QueryArgs:
    reverse = False


class BaseDAO:
    json = True
    model = None
    working_instance = object
    exclusions = []
    relationships = True
    sortkey = 'id'
    queryargs = QueryArgs()
    querystring = None  # TODO Break out this code to a class and encapsulate mapping a little better
    _actions = ActionsModel

    def __init__(self, model=None, *args, **kwargs):
        setattr(self.queryargs, 'reverse', False)
        self.model = model or self.model
        if kwargs.get('querystring'):
            self.__querystring(kwargs.get('querystring'))

    def actions(self):
        return self._actions

    def schema(self, exclude=None):
        if not exclude:
            exclude = []
        return self.model.schema(exclude=self.exclusions + exclude, rel=self.relationships)

    def __querystring(self, querystring):
        fields = []
        for key, value in querystring.items():
            if value[0] == 'false':
                fields.append(key)
        self.exclusions = [i for i in list(fields)]

        rels = querystring.get('relationships', True)
        if rels:
            self.relationships = rels not in ['false', 'N', 'no', 'No', '0']

        order = querystring.get('order_by', False)
        if order:
            if order not in self.model.keys():
                raise ValueError('This field is not a recognised sort field.')
            self.sortkey = order

        return self.exclusions

    @classmethod
    def model_schema(cls, exclude=None):
        return cls.model.get_schema(exclude=exclude)

    def validate_arguments(self, payload):
        valid_fields = dir(self.model)
        valid = True
        invalid_fields = []

        for item in payload:
            if item not in valid_fields:
                invalid_fields.append(item)
                valid = False

        if valid is False:
            raise ValueError('<{}> not accepted as input field(s)'.format(', '.join(invalid_fields)))
        return True

    def __query(self):
        query = self.model.makequery()
        return query

    def __buffer(self, flagged=False):
        query = self.model.makequery()
        return QueryBuffer(query, self.model, view_flagged=flagged, rel=self.relationships, dao=self)

    def query(self, flagged=False):
        buffer = QueryBuffer(self.__query(), self.model, view_flagged=flagged, rel=self.relationships, dao=self)
        buffer.order_by(self.sortkey, self.queryargs.reverse)
        return buffer

    def delete(self, instanceid):
        instance = self.get_one(instanceid).view()
        clone = copy.deepcopy(instance)
        instance.delete()
        return clone

    def get_one(self, value, flagged=False):
        pkfilter = {self.model.id: value}
        query = self.model.makequery()
        buffer = QueryBuffer(query, self.model, view_flagged=flagged)
        return buffer.filter(pkfilter).first()

    def get_all_by(self, field, value, flagged=False):
        pkfilter = {field: value}
        query = self.model.makequery()
        buffer = QueryBuffer(query, self.model, view_flagged=flagged)
        return buffer.filter(pkfilter).all()

    def get_one_by(self, field, value, flagged=False):
        pkfilter = {field: value}
        query = self.model.makequery()
        buffer = QueryBuffer(query, self.model, view_flagged=flagged)
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
        try:
            payload['created'] = datetime.now()
            instance = self.model.create(**payload)
            return DataBuffer(self.save(instance), instance.schema(), None)
        except sqlalchemy.exc.IntegrityError as error:
            model = str(self.model.__tablename__).capitalize()
            errorfield = ''
            try:
                errorfield = str(error.orig).split(':')[1].split('.')[1]
            except Exception:
                errorfield = ''
            message = 'Cannot create {0}. A {0} with {1} \'{2}\' already exists.'.format(
                model, errorfield.capitalize(), payload.get(errorfield)
            )
            raise HTTPException(
                message=message,
                code=409
            )

    def save(self, instance):
        try:
            instance.save(_commit=True)
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
