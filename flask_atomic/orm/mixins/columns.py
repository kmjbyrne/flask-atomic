from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import func


class PrimaryKeyMixin:
    id = Column(Integer, primary_key=True)


class CreationTimestampMixin:
    created = Column(DateTime, default=func.now())


class UpdateMixin:
    updated = Column(DateTime, default=func.now())
