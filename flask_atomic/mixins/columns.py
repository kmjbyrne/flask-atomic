from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import func


class PrimaryKeyMixin:
    id = Column(Integer, primary_key=True)


class LabelMixin:
    label = Column(String(256), default='')


class CreationTimestampMixin:
    created = Column(DateTime, default=func.now())


class UpdateMixin:
    updated = Column(DateTime, default=func.now())


class ActiveMixin:
    active = Column(String(5), default='Y')


class StatusMixin:
    status = Column(String(5), default='Y')


class SuperMixin(PrimaryKeyMixin, CreationTimestampMixin, UpdateMixin, ActiveMixin):
    __abstract__ = True
