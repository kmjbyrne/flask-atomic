Basic Usage
============

Lets start with a basic usage example and illustrate the core features Flask Atomic offers.

Architect Blueprint
-------------------

The Architect Blueprint is itself yes, you guessed it a Flask Blueprint. It looks, smells and
sounds just the same as a normal Flask Blueprint but does a little magic for you.

We just need an SQLAlchemy Model to get things started.

    .. code-block::

        class SomeModel(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.Datetime, default=datetime.now())
            username = db.Column(db.String(50))
            alias = db.Column(db.String(50))


When we have models like this we typically will have a GET route, POST route maybe DELETE and
PUT depending on the application. Typically, these routes will have similar behaviours across
different application: define a route, take some data, create a model, save to database.

    .. code-block::

        from flask_atomic import Architect

        from .models import SomeModel

        app = Flask(__name__)
        module = Architect(SomeModel)
        app.register_blueprint(module, url_prefix='example')

        if __name__ == '__main__':
            app.run()

What has been created?

+---------------------------+--------+-----------------------------------------------------------------------+
| Route                     | Method | Comment                                                               |
+===========================+========+=======================================================================+
| /example                  | GET    | Index endpoint for the model, fetches all data.                       |
+---------------------------+--------+-----------------------------------------------------------------------+
| /example/:resource        | GET    | Get one endpoint. Defaults to model primary key.                      |
+---------------------------+--------+-----------------------------------------------------------------------+
| /example/:resource/:field | GET    | Get one endpoint, returning field. Can be relationships.              |
+---------------------------+--------+-----------------------------------------------------------------------+
| /example                  | POST   | Post endpoint that allows for creation of new records.                |
+---------------------------+--------+-----------------------------------------------------------------------+
| /example/:resource        | DELETE | Delete endpoint, defaults to deleting :resource based on PK lookup.   |
+---------------------------+--------+-----------------------------------------------------------------------+
| /example/:resource        | PUT    | Put endpoint that allows for making modifications to a record.        |
+---------------------------+--------+-----------------------------------------------------------------------+
| /example/:resource        | HEAD   | Simply checks a record exists and returns HTTP 200 if so, 404 if not. |
+---------------------------+--------+-----------------------------------------------------------------------+
Making a curl request to your API and see it in action:

`curl localhost:5000/example`

Using the example model above, lets check posting new records:

    .. code-block::

        curl --header "Content-Type: application/json" \
          --request POST \
          --data '{"name":"xyz","username":"xyz","alias":"xyz}' \
          http://localhost:5000/example


Multiple Models
---------------

The Blueprint can accept multiple models also. The only difference is that the model name
will be used as a suffix to the prefix provided at instantiation.

    .. code-block::

        from flask_atomic import Architect

        from .models import SomeModel
        from .models import OtherModel

        app = Flask(__name__)
        module = Architect([SomeModel, OtherModel])
        app.register_blueprint(module, url_prefix='example')

        if __name__ == '__main__':
            app.run()

What has been created?

.. csv-table::
    :header: "Route", "Method", "Note"
    :widths: 15, 10, 30

    "/example/some_model", "GET", "Index"
    "/example/some_model/:resource", "GET", ""
    "/example/some_model/:resource/:field", "GET"
    "/example/some_model", "POST", "Index"
    "/example/some_model/:resource", "DELETE", "Index"
    "/example/some_model/:resource", "PUT", "Index"
    "/example/some_model/:resource", "HEAD", "Index"
    "/example/other_model", "GET", "Index"
    "/example/other_model/:resource", "GET"
    "/example/other_model/:resource/:field", "GET"
    "/example/other_model", "POST", "Index"
    "/example/other_model/:resource", "DELETE", "Index"
    "/example/other_model/:resource", "PUT", "Index"
    "/example/other_model/:resource", "HEAD", "Index"

