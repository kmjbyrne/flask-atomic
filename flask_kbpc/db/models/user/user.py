from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

from flask_kbpc.db.flaskalchemy.database import DeclarativeBase

db = SQLAlchemy()


class BaseUser(DeclarativeBase):
    __tablename__ = 'user'
    __abstract__ = True
    created = db.Column(db.DateTime())
    username = db.Column(db.String(120), unique=True)
    forename = db.Column(db.String(120))
    surname = db.Column(db.String(120))
    password = db.Column(db.Text, nullable=False)
    admin = db.Column(db.String(5))

    def __init__(self, **kwargs):
        super(BaseUser, self).__init__(**kwargs)
        self.created = datetime.now()

    def name(self):
        return '{} {}'.format(self.forename, self.surname)
