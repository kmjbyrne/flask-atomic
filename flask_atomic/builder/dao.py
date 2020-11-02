from datetime import datetime

from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy_blender.helpers import columns
from sqlalchemy_blender.helpers import relationships
from sqlalchemy_blender.helpers import primarykey

from flask_atomic.database import db

from handyhttp.exceptions import HTTPConflict
from handyhttp.exceptions import HTTPBadRequest
from handyhttp.exceptions import HTTPNotFound
from handyhttp.exceptions import HTTPNotProcessable


def getsession():
    db = current_app.extensions['sqlalchemy'].db
    return db.session


class ModelDAO:

    def __init__(self, model=None, autoupdate=True, *args, **kwargs):
        self.model = model
        self.autoupdate = autoupdate

    def one(self, value, key=None):
        if not key:
            key = self.model.__mapper__.primary_key[0].name
        filter_expression = {key: value}
        query = self.model.query.filter_by(**filter_expression)
        return query.first()

    def validate_arguments(self, payload):
        valid_fields = dir(self.model)
        invalid_fields = []

        for item in payload:
            if not getattr(self.model, item, None):
                invalid_fields.append(item)
        if list(filter(lambda field: not field.startswith('_'), invalid_fields)):
            err = f'<{invalid_fields}> not accepted fields'
            raise HTTPBadRequest(err)

        for item in  [i for i in payload.keys() if i.startswith('_')]:
            del payload[item]
        return True

    def commit(self, operation, instance):
        session = getsession()
        try:
            session = current_app.extensions['sqlalchemy'].db.session
            getattr(session, operation)(instance)
            session.commit()
            return instance
        except IntegrityError as exc:
            session.rollback()
            if exc.orig.args[0] == 1452:
                raise HTTPNotProcessable()
            raise HTTPConflict(str(exc.orig.args[1]))
        except Exception as exc:
            session = current_app.extensions['sqlalchemy'].db.session
            try:
                local_object = session.merge(session)
                session.add(local_object)
                session.commit()

                session = session.object_session()
                getattr(session, operation)(instance)
                session.commit()
            except Exception:
                session.rollback()
                session.flush()
                # session.closed()

    def delete(self, instance):
        if not instance:
            raise HTTPNotFound()
        return self.commit('delete', instance)

    def save(self, instance):
        self.commit('add', instance)
        return instance

    def create(self, payload, json=False, **kwargs):
        self.validate_arguments(payload)
        _payload = {}
        _keys = set([key for key in payload.keys() if not key.startswith('__')])
        for item in set([i.key for i in relationships(self.model)]).intersection(_keys):
            actual = getattr(relationships(self.model), item).primaryjoin.right.name
            _payload[actual] = None
            _payload[item] = None
            if isinstance(payload.get(item), list):
                current = payload.get(item)
                _payload[actual] = []
                for data in payload.get(item):
                    pk = primarykey(getattr(relationships(self.model), item).entity.entity)
                    # current.get(primarykey(getattr(relationships(self.model), item).entity.entity))
                    _payload[actual].append(data.get(pk))
            else:
                _payload[actual] = payload.get(item).get(primarykey(getattr(relationships(self.model), item).entity.entity))
            _payload[item] = payload.get(item)
            del payload[item]
        instance = self.model(**payload)

        if 'user' in kwargs.keys() and 'creator_id' in columns(self.model, strformat=True):
            instance.creator_id = kwargs.get('user')

        self.update(instance, _payload)
        return self.save(instance)

    def update(self, instance, payload, **kwargs):
        fields = columns(instance, strformat=True)
        rels = relationships(instance)
        for attr, value in payload.items():
            if attr != 'id' and attr in fields:
                if str(getattr(instance.__mapper__.columns, attr).type) == 'DATETIME' and isinstance(value, bool):
                    value = datetime.now()
                # only change fields with a value delta
                if getattr(instance, attr) != value:
                    setattr(instance, attr, value)

        for mtm in set([i.key for i in rels]).intersection(set(payload.keys())):
            model = getattr(instance, mtm)

            if not model:
                _instance = getattr(instance.__mapper__.relationships, mtm).entity.entity
                _lookup = mtm

                if isinstance(payload.get(mtm), dict):
                    _lookup = payload.get(mtm).get('id', None)

                elem = self.session().query(_instance).get(_lookup)
                if not elem:
                    continue
                setattr(instance, f'{mtm}_id', elem.id)
                continue

            if not isinstance(model, list):
                setattr(instance, mtm, model)
                continue
            current = set(map(lambda rel: getattr(rel, rel.identify_primary_key()), model))
            candidates = set(map(lambda item: list(item.values()).pop(), kwargs[mtm]))
            for addition in candidates.difference(current):
                association = self.session().query(instance.__mapper__.relationships.classgroups.entity).get(addition)
                getattr(instance, mtm).append(association)

            for removal in current.difference(candidates):
                association = self.session().query(instance.__mapper__.relationships.classgroups.entity).get(removal)
                getattr(instance, mtm).remove(association)

        if self.autoupdate:
            if getattr(instance, 'updated', None):
                setattr(instance, 'updated', datetime.now())
        self.save(instance)
        return instance

    def softdelete(self, instance, flag):
        instance.active = flag
        self.save(instance)
