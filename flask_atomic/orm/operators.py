from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import OperationalError

from flask_atomic.logger import getlogger
from flask_atomic.orm.database import db

logger = getlogger(__name__)


def commitsession():
    try:
        db.session.commit()
        return
    except OperationalError as operror:
        logger.info(str(operror))
        db.session.rollback()
        db.session.close()
    except IntegrityError as integerror:
        raise integerror
    except Exception:
        raise Exception
    finally:
        logger.info(str('DB execution cycle complete'))
