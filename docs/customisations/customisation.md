Customisations
==============

## Explicit Methods

To define an explicit list of methods that are available, the Blueprint accepts
a collection of `methods`.

If we only wish to expose `GET` methods for the Blueprint for example, we would
simply pass `methods=['GET']` to the Blueprint, like so:

```python
from flask_atomic import Architect

from .models import SomeModel

app = Flask(__name__)
module = Architect(SomeModel)
app.register_blueprint(module, url_prefix='example', methods=['GET'])

if __name__ == '__main__':
    app.run()
```

## Data Access Object

For `POST`, `DELETE` requests, the endpoints utilise a Data Access Object (DAO) to
CRUD the models. The DAO acts as an intermediate object between the database and the
application. If you wish to override this intermediate, you can simply pass `dao=CustomDAO`
to the instance.

    Note: there are some assumptions about the DAO e.g it must have *delete* and *create* methods.

Easiest tactic here would be to sub class the DAO class and then provide custom implementations
that will be leveraged in the endpoints.

```python
from flask_atomic import ModelDAO

from .models import SomeModel


class CustomDAO(ModelDAO):
    def create(payload):
        # some custom override features
        super().create(payload)


app = Flask(__name__)
module = Architect(SomeModel)
app.register_blueprint(module, url_prefix='example', dao=CustomDAO)

if __name__ == '__main__':
    app.run()
```

## Configuration Driven

There are some constraints with using the default instance. For example, perhaps you want to do
your own thing on a `POST` request or some logging.

Additionally, the default instance will use the primary key as a lookup field for any **:resource**
requests. If you wish to use another field as a lookup, the you will need to provide a configuration
object.

The following example includes an overridden **create** function on a CustomDAO that extends ModelDAO.
The lookup key is defined also and the model is declared in the configuration also.

```python
from flask_atomic import ModelDAO

from .models import SomeModel


class CustomDAO(ModelDAO):
    def create(payload):
        # some custom override features
        raise ValueError()


config = [
    dict(model=SomeModel, dao=CustomDAO, key=SomeModel.id.name)
]


app = Flask(__name__)
module = Architect(SomeModel)
app.register_blueprint(module, url_prefix='example', dao=CustomDAO)

if __name__ == '__main__':
    app.run()
```

Running a `POST` request will raise a ValueError. Not exactly useful but illustrates the custom feature.

One common use case for this type of extension is to override the **delete** operator and then set a flag
in the record to something like `D` that acts as a soft-delete instead of actually deleting the record from
the database.
