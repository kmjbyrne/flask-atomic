import copy

from datetime import datetime
from urllib import parse

import sqlalchemy

from flask_electron.db.flaskalchemy.database import DeclarativeBase
from flask_electron.dao.actions import ActionsModel
from flask_electron.dao.query import QueryBuffer
from flask_electron.http.exceptions import HTTPException


class BaseDAO:
    json = True
    model = DeclarativeBase
    working_instance = object
    exclusions = []
    relationships = False
    sortkey = None
    querystring = None
    _actions = ActionsModel

    def __init__(self, *args, **kwargs):
        if kwargs.get('querystring'):
            self.__querystring(kwargs.get('querystring'))

    def actions(self):
        return self._actions

    def schema(self, exclude=None):
        if not exclude:
            exclude = []
        return self.model.get_schema(exclude=self.exclusions + exclude)

    def __querystring(self, query_string):
        args = parse.parse_qs(query_string.decode('utf-8'), encoding='utf-8')
        fields = []
        for key, value in args.items():
            if value[0] == 'false':
                fields.append(key)
        self.exclusions = [i for i in list(fields)]

        rels = args.get('relationships', None)
        if rels:
            if rels[0] == 'true':
                self.relationships = True
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

        if valid is False:
            raise ValueError('<{}> not accepted as input field(s)'.format(', '.join(invalid_fields)))
        return True

    def __query(self):
        query = self.model.makequery()
        return query

    def __buffer(self, flagged=False):
        query = self.model.makequery()
        return QueryBuffer(query, self.model, view_flagged=flagged)

    def query(self, flagged=False):
        return QueryBuffer(self.__query(), self.model, view_flagged=flagged)

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
            instance = self.model.create(**payload)
            instance.save()
            return instance
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
            instance.save()
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

        instance = self.get_one(instance_id).view()
        instance.active = 'D'
        instance.save()
        return instance