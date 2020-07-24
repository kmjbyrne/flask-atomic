from sqlalchemy import Column, Integer, String


from flask_atomic.db import DeclarativeBase


class TestModel(DeclarativeBase):
    __tablename__ = 'tester'
    name = Column(String(256), nullable=True)
