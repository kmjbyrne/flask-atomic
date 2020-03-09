from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError

from flask_atomic.logger import getlogger
from flask_atomic.orm.database import db


def commitsession():
    try:
        db.session.commit()
        return
    except OperationalError as operror:
        db.session.rollback()
        db.session.close()
    except IntegrityError as integerror:
        raise integerror
    except Exception:
        raise Exception
