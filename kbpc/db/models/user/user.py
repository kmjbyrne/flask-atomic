from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

from kbpc.db.flaskalchemy.database import DeclarativeBase

db = SQLAlchemy()


class User(db.Model, DeclarativeBase):
    __tablename__ = 'user'
    created = db.Column(db.DateTime())
    username = db.Column(db.String(120), unique=True)
    forename = db.Column(db.String(120))
    surname = db.Column(db.String(120))
    password = db.Column(db.Text, nullable=False)
    admin = db.Column(db.String(5))

    def __init__(self, **kwargs):
        super(**kwargs)
        self.created = datetime.now()

    def name(self):
        return '{} {}'.format(self.forename, self.surname)
