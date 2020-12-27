from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
FIXED_TABLENAME = 'example'
SECOND_TABLENAME = 'second'


class ExampleModel(db.Model):
    __tablename__ = FIXED_TABLENAME
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(256), nullable=True)
    related = db.relationship('AnotherModel', cascade='all, delete', backref=db.backref('examples', lazy=True))
    related_id = db.Column(db.Integer, db.ForeignKey(f'{SECOND_TABLENAME}.id'), nullable=True)


class AnotherModel(db.Model):
    __tablename__ = SECOND_TABLENAME
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(256), nullable=True)
