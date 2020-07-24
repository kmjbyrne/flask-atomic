from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from flask_sqlalchemy import SQLAlchemy

base = declarative_base()


class DeclarativeBase(base):
    __abstract__ = True
    uid = Column(Integer, primary_key=True, autoincrement=True)

