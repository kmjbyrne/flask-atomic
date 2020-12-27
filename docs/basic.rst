Basic Usage
============

Lets start with a basic usage example and illustrate the core features Flask Atomic offers.

Architect Blueprint
++++++++++++++++++++

The Architect Blueprint is itself yes, you guessed it a Flask Blueprint. It looks, smells and
sounds just the same as a normal Flask Blueprint but does a little magic for you.

All that's needed to start is a SQLAlchemy Model to get things started.


    .. code-block:: python

        class SomeModel(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.Datetime, default=datetime.now())
            username = db.Column(db.String(50))
            alias = db.Column(db.String(50))

When we have models like this we typically will have a GET route, POST route maybe DELETE and
PUT depending on the application. Typically, these routes will have similar behaviours across
different application: define a route, take some data, create a model, save to database.

    .. code-block:: python

        from flask_atomic import Architect

        from .models import SomeModel

        monitor_blueprint = Architect(SomeModel)

        app = Flask(__name__)
        app.register_blueprint(monitor_blueprint, url_prefix='example')

        if __name__ == '__main__':
            app.run()

What has been created?

1. GET /example (index)
2. GET /example/<resource> (get one)
3. GET /example/<resource>/<field> (get one and fetch field)
4. POST /example (accepts fields and creates entries in database)
5.


Curl your API and see it in action:

localhost:5000/access
