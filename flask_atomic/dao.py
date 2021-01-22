from datetime import datetime

from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy_blender.helpers import columns
from sqlalchemy_blender.helpers import relationships

from handyhttp.exceptions import HTTPConflict
from handyhttp.exceptions import HTTPNotFound
from handyhttp.exceptions import HTTPNotProcessable
from handyhttp.exceptions import HTTPBadRequest


def getsession():
    db = current_app.extensions['sqlalchemy'].db
    return db.session


class ModelDAO:

    def __init__(self, model=None, autoupdate=True, session=None, *args, **kwargs):
        self.model = model
        self.autoupdate = autoupdate
        self.__session = session

    def session(self):
        if not self.__session:
            db = current_app.extensions['sqlalchemy'].db
            return db.session
        return self.session()

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
        if invalid_fields:
            err = f'<{invalid_fields}> not accepted fields'
            raise HTTPBadRequest(msg=err)

        return True

    def commit(self, operation, instance):
        session = self.session()
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
        except ProgrammingError as exc:
            if exc.orig.args[0] == 1064:
                raise HTTPNotProcessable(str(exc))
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
        if self.autoupdate:
            if getattr(instance, 'updated', None):
                setattr(instance, 'updated', datetime.now())
        self.commit('add', instance)
        return instance

    def create(self, payload, json=False, **kwargs):
        self.validate_arguments(payload)
        _payload = {}
        _keys = set([key for key in payload.keys() if not key.startswith('__')])
        for item in set([i.key for i in relationships(self.model)]).intersection(_keys):
            actual = getattr(relationships(self.model), item).primaryjoin.right.name
            _payload[actual] = payload.get(item)
            _payload[item] = payload.get(item)
            del payload[item]

        instance = self.model(**payload)
        if 'user' in kwargs.keys() and 'creator_id' in columns(self.model, strformat=True):
            instance.creator_id = kwargs.get('user')

        self.update(instance, _payload)
        self.save(instance)
        return instance

    def remove(self, instance, item):
        getattr(instance, item).remove(item)

    def update(self, instance, payload, **kwargs):
        fields = columns(instance, strformat=True)
        rels = relationships(instance)
        for attr, value in payload.items():
            if attr != 'id' and attr in fields:
                if str(getattr(instance.__mapper__.columns, attr).type) == 'DATETIME' and isinstance(value, bool):
                    value = datetime.now()
                setattr(instance, attr, value)

        for mtm in set([i.key for i in rels]).intersection(set(payload.keys())):
            model = getattr(instance, mtm)

            if not model and not isinstance(model, list):
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
                _instance = getattr(instance.__mapper__.relationships, mtm).entity.entity

                _lookup = value
                if not isinstance(value, int):
                    _lookup = payload.get(mtm).get('id', None)
                elem = self.session().query(_instance).get(_lookup)
                setattr(instance, mtm, elem)
                continue

            # current = set(map(lambda rel: getattr(rel, rel[0].__mapper__.primary_key[0].name), model))
            current = set(map(lambda item: getattr(item, 'id'), model))
            candidates = set(map(lambda item: item.get('id'), payload[mtm]))
            for addition in candidates.difference(current):
                association = self.session().query(
                    getattr(instance.__mapper__.relationships, mtm).entity
                ).get(addition)
                getattr(instance, mtm).append(association)

            for removal in current.difference(candidates):
                association = self.session().query(
                    getattr(instance.__mapper__.relationships, mtm).entity
                ).get(removal)
                getattr(instance, mtm).remove(association)

        self.save(instance)
        return instance

    def softdelete(self, instance, flag):
        instance.active = flag
        self.save(instance)
