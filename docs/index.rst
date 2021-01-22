Flask Atomic
====================

Flask Atomic leverages the power of Flask Blueprints & SQLAlchemy to provide a plugin
application builder. Blueprints are essentially mini Flask applications that
are registered to the Flask application. Encapsulated within these Blueprints
are all routes, templates etc...

When developing Flask applications and working with large amounts of models where
boilerplate CRUD operations are required. With well-defined code, Flask Atomic has
the opportunity to render potentially hundreds of lines of redundant.

This project was heavily influenced by repetitive efforts to get quick and dirty
APIs up and running, with the bad practice of re-using a lot of code, over and over
again. Instead of relying on throwaway efforts, Flask Atomic provides a very
simply means to abstract away code and enable RESTful API best practices that
are often esoteric and difficult to engineer for small projects.

This library also contains a few helpers and other utilities that I have found helpful.

This library depends on SQLAlchemyBlender and HandyHTTP for extended features.


.. toctree::
    installation
    basic
    customisations/customisation.md
    recipes


API
===

.. toctree::
    :maxdepth: 2


Indices and tables
__________________

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
