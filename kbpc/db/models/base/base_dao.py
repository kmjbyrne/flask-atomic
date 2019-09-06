import sqlalchemy

from kbpc.db.flaskalchemy.database import DeclarativeBase
from kbpc.http.utils.exceptions import HTTPException


class BaseDAO:
    json = True
    model = DeclarativeBase
    working_instance = object

    def schema(self, exclude=None):
        return self.model.get_schema(exclude=exclude)

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

    def get(self, rel=False, json=True, exc=None, order=None, limit=0):
        if exc is None:
            exc = list()

        data = self.model.get(limit=limit, order=order)
        return list(
            i.prepare(
                rel=rel,
                exc=exc,
                json=json
            ) for i in data or []
        )

    def get_one(self, value, rel=False, json=True):
        data = self.model.get_one_by_field(str(self.model.id.key), value)
        if not data:
            return None
        return data.prepare(rel=rel, json=json)

    def get_all_by(self, field, value, limit=0, json=True):
        articles = [i.prepare(rel=False, json=json) for i in self.model.get_all_by_field(self.model.getkey(
            field), value)]
        return articles

    def get_one_by(self, field, value, json=True):
        data = self.model.get_one_by_field(self.model.getkey(field), value)
        if data:
            return data.prepare(rel=False, json=json)
        return None

    def create(self, payload):
        self.validate_arguments(payload)
        instance = self.model.create(**payload)
        return instance

    def save(self, instance):
        try:
            instance.save()
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException('Resource with part or all of these details already exists', code=409)

    def update(self, instance_id, payload):
        instance = self.get_one(instance_id, json=False)
        instance.update(**payload)
        instance.save()
        return instance

    def delete(self, instance_id):
        instance = self.get_one(instance_id, json=False)
        instance.active = 'D'
        instance.save()
        return instance
