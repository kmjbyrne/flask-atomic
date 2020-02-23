import os

from flask import Flask
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from flask_atomic.blueprint.core import CoreBlueprint
from flask_atomic.orm.base import DeclarativeBase
from flask_atomic.orm.database import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join('/tmp', 'database.db')
db.init_app(app)


class MyModel(DeclarativeBase):
    _id = Column(Integer, primary_key=True)
    label = Column(String(256))

    def __str__(self):
        return 'A Description of the Model'


blueprint = CoreBlueprint(
    'blueprint_name',
    __name__,
    MyModel
)

if __name__ == '__main__':
    app.app_context().push()
    db.create_all()
    db.session.commit()
    app.register_blueprint(blueprint, url_prefix='/access')
    app.run(port=5000, debug=True)
