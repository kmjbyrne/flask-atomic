Quickstart
=========================

    .. note::

        Package was developed using Python 3.6. No guarantee is given for
        backwards compatibility with older versions of Python. Especially
        Python < 3.x. If you have to ask if this works with Python 2,
        perhaps you should consider migrating.


    .. warning::

        This guide assumes a foundation understanding of Flask and Blueprints.
        Blueprints are essentially smaller application units that fit into the
        larger Flask application instance. This is akin to 'apps' in Django.


Installation
------------

From the PyPi repository `pip install Flask-Atomic`

Minimal Example
---------------

Much of immediate Flask code is completely boiler-plate and often repeated
from other projects, in terms of similarity.

Consider the scenario where you may have a model, and simply want to provide
a GET request endpoint to fetch all the data for that model. Sounds easy, right?

From a high level, this is not a complex problem. Let's revisit our scenario:

We have a model defined with the SQLAlchemy ORM like so:

    .. code-block:: python

        ....

        class YourSuperModel(db.Model):
            name = db.Column(db.Datetime, default=datetime.now())
            username = db.Column(db.String(50))
            alias = db.Column(db.String(50))

        ...


Typically, you would approach this like so:

    .. code-block:: python

        from flask import jsonify

        from models import SomeMonitoringModel

        app = Flask(__name__)

        @app.route('/model-url', methods=['GET'])
        def monitoring_index():
            data = YourSuperModel.query().all()
            resp = list
            for item in data:
                resp.append(
                    dict(
                        name=item.name
                        username=item.username
                        alias=item.alias
                    )
                )
            return jsonify(data=resp)

This is only a single endpoint. POST endpoints are 3-4 times bulkier.

The Magic
+++++++++

What if this could simply be abstracted away. First, binding the model. Let
DeclarativeBase be the db session instance. Just be sure to bind it to the
root application or the models will not be created in the database.

    .. code-block:: python

        from flask_atomic.orm.declaratives.base import DeclarativeBase


        class YourSuperModel(DeclarativeBase):
            name = db.Column(db.Datetime, default=datetime.now())
            username = db.Column(db.String(50))
            alias = db.Column(db.String(50))
        ...


Next, putting together the Blueprint and model.

    .. note::

        Some assumptions about project directory are being made here. Please
        tailor to your standards. Flask has a general guideline for Blueprint
        directory structure that works well.


    .. code-block:: python


        from flask_atomic.blueprint.core import CoreBlueprint

        from .models import YourSuperModel

        monitor_blueprint = CoreBlueprint(
            'supermodel',
            __name__,
            YourSuperModel
        )

        ...

        app = Flask(__name__)
        app.register_blueprint(monitor_blueprint, url_prefix='supermodel')

        if __name__ == '__main__':
            app.run()


And that is a minimal example. So what did this code do?

* Import CoreBlueprint
* Setup CoreBlueprint, providing BP name, module and your model.
* Create Flask app as normal.
* Register the blueprint with the app instance.
* Run.

GET, POST, PUT, DELETE endpoints are now accessible by via HTTP.

`HTTP GET localhost:5000/access`

You now have four endpoints, tested and ready. These endpoints work in the same
way. Lets consider a POST request.

`HTTP POST localhost:5000/access`

    .. code-block:: json
        {
            "entry_date": "2020-01-01 00:00:00",
            "source": "some data"
            "destination": "some other data"
            "status": "Active"
        }

By using Postman, CURL or HTTPie, try out the endpoints. The above, will create
a new monitor record in the database you have configured your application to run
with. For the sake of illustration, consider using a SQLite database instance
setup in your `/tmp` directory. Create a model, and start querying your data.
