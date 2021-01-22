from flask_sqlalchemy import SQLAlchemy

from flask_atomic import ModelDAO

db = SQLAlchemy()
FIXED_TABLENAME = 'example'
SECOND_TABLENAME = 'second'


class CustomDAO(ModelDAO):

    def create(self, payload):
        payload['label'] = 'different value than posted'
        return super().create(payload)

    def delete(self, instance):
        instance.state = 'D'
        self.session().commit()
        return instance


class ExampleModel(db.Model):
    __tablename__ = FIXED_TABLENAME
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(256), nullable=True)
    related = db.relationship('AnotherModel', cascade='all, delete', backref=db.backref('examples', lazy=True))
    related_id = db.Column(db.Integer, db.ForeignKey(f'{SECOND_TABLENAME}.id'), nullable=True)
    state = db.Column(db.String(1), nullable=True, default='Y')


class AnotherModel(db.Model):
    __tablename__ = SECOND_TABLENAME
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(256), nullable=True)
