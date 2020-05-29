from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import DataError

from flask_atomic.logger import getlogger
from flask_atomic.orm.database import db

DATA_ERROR = 'Value provided for {} is too large.'
EXCMAP = {
    '9h9h': lambda x: DATA_ERROR.format(str(str(x).split('\'').pop(1)).capitalize())
}


def __process_error(err, info):
    db.session.rollback()
    raise ValueError(info)


def commitsession():
    try:
        db.session.commit()
        return
    except OperationalError as operror:
        db.session.rollback()
        db.session.close()
    except IntegrityError as integerror:
        db.session.rollback()
        raise integerror
    except DataError as error:
        db.session.rollback()
        return __process_error(error, EXCMAP[error.code](error))
    except Exception as error:
        db.session.rollback()
        raise Exception
