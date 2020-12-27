Flask Atomic
====================

REST API development should be quick and painless, especially when prototyping
or working with large amounts of models where boilerplate CRUD operations are
required. With well-defined code, Flask Atomic has the opportunity to render
potentially hundreds of lines of redundant.

This project was heavily influenced by repetitive efforts to get quick and dirty
APIs up and running, with the bad practice of re-using a lot of code, over and over
again. Instead of relying on throwaway efforts, Flask Atomic provides a very
simply means to abstract away hundreds of lines of code and enable RESTful API best
practices that are often esoteric and difficult to engineer for small projects.

This project intended to be a building block to enrich the Flask ecosystem,
without compromising any Flask functionality. Leaving you to integrate without
issues, breathing life into your projects in less than 5 lines of code. Feature
rich but non-assuming.

The Flask Atomic package can be used for:

* Blueprint integration for creating main HTTP method endpoints.
* Extensible data access objects for common database interactions.
* Automatic query string processing engine for requests.
* Fully dynamic model schema definitions without any hardcoding.
* SQLAlchemy model serializer for transforming Models to JSON ready format.
* Custom JSON response partials to reduce repetitive Flask.jsonify responses.
* Variety of db model mixins, including DYNA flag columns and primary key column.



.. toctree::
    installation



API
===

.. toctree::
    :maxdepth: 2


Indices and tables
__________________

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
