from flask import current_app


db = current_app.extensions['sqlalchemy'].db
session = current_app.extensions['sqlalchemy'].db.session
