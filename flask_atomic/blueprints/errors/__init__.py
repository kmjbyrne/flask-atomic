from flask import Blueprint

error_handler = Blueprint(
    'errors',
    __name__,
)

from . import handler