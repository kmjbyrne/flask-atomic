## Database Helpers

### Flask Alchemy Model Serializer


Transformation was originally a series of routines written to convert FlaskAlchemy models into jsonifiable dict 
structures. This proved to be a solution lacking elegance and evolved and eventually found its way into half a dozen 
projects over time and eventually, then started to splinter into slightly different variations.

#### Basic Usage

```python
from flask import jsonify

from application.models import SomeFlaskAlchemyModel
from swiss import models

# Assume the model has name and age as the model fields
model = SomeFlaskAlchemyModel('John Doe', 25)
transformed_model = models.unpack(model)

# This typically fails if you attempt it with the model.
json = jsonify(data=model)

# This however is serializable immediately
json = jsonify(data=transformed_model)
```


Often, fields like passwords or other sensitive data should be hidden from responses or outputs. Usually this would be 
managed at the model class, and writing a to_dict() function or something similar, and simply not declaring the 
protected properties of that instance.

#### Protected Properties

```python
from flask import jsonify

from application.models import SomeFlaskAlchemyModel
from swiss import models

# Assume the model has name and age as the model fields
model = SomeFlaskAlchemyModel('John Doe', 25)
tablename = 'tablename_of_model'
exclusions = {tablename: ['age'])
transformed_model = models.unpack(model, exclusions)

# This however is serializable immediately
json = jsonify(data=transformed_model)
```
