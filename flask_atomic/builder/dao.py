from datetime import datetime

from flask import current_app
from sqlalchemy.exc import IntegrityError
from ..database import db
from ..http.exceptions import HTTPConflict
from ..http.exceptions import HTTPBadRequest
from ..http.exceptions import HTTPNotFound


class ModelDAO:

    def __init__(self, model, *args, **kwargs):
        self.model = model

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
            raise HTTPBadRequest(err)

        return True

    def save(self, instance):
        try:
            db.session.add(instance)
            db.session.commit()
        except Exception as error:
            from flask import current_app
            session = current_app.extensions['sqlalchemy'].db.session
            session.add(instance)
            session.commit()
            # err = f'{str(instance).capitalize()} with part or all of these details already exists'
            # raise HTTPConflict(err)
        return instance

    def create(self, payload, json=False):
        self.validate_arguments(payload)
        instance = self.model(**payload)
        return self.save(instance)

    def update(self, instance, payload):
        if 'last_update' in instance.fields():
            payload.update(last_update=datetime.now())
        instance.update(**payload)
        instance.save()
        return instance

    def softdelete(self, instance, flag):
        instance.active = flag
        self.db.session.merge(instance)
        self.db.session.commit()

    def delete(self, instance):
        if instance:
            instance._sa_instance_state.session.close()
        else:
            raise HTTPNotFound()
        self.db.session.delete(instance)
        self.db.session.commit()



