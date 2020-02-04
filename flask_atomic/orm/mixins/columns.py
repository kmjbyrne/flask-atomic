from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import func


class PrimaryKeyMixin(object):
    id = Column(Integer, primary_key=True)


class CreationTimestampMixin(object):
    created = Column(DateTime, default=func.now())
