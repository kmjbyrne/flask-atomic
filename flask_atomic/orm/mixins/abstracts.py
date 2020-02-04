from sqlalchemy import Column
from sqlalchemy import String

from flask_atomic.orm.operators import commitsession


class DYNAFlagMixin(object):
    """
    DYNA stands for (in context of the 'active' field)

    D - Deleted
    Y - Yes
    N - No (inactive, i.e suspended)
    A - Approval required

    This is only a suggested pattern for soft database deletion. Just a sensible
    rule is that nothing should really be deleted from a database by a user.

    Database deletions should be handled by application owners or data owners.
    Allowing customers to modify the existence of data is not good.
    """

    active = Column(String(1), default='Y')

    def can_commit(self, commit=True):
        if commit:
            commitsession()
        return self

    def safe_delete(self, commit=True):
        self.active = 'D'
        return self.can_commit(commit)

    def deactivate(self, commit=True):
        self.active = 'N'
        return self.can_commit(commit)

    def restore(self, commit=True):
        self.active = 'Y'
        return self.can_commit(commit)
