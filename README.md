# Flask Atomic

![GitHub](https://img.shields.io/github/license/kmjbyrne/flask-atomic)
[![PyPI version](https://badge.fury.io/py/Flask-Atomic.svg)](https://badge.fury.io/py/Flask-Atomic)
[![Build Status](https://travis-ci.org/kmjbyrne/flask-atomic.svg?branch=master)](https://travis-ci.org/kmjbyrne/flask-atomic)
[![Coverage Status](https://coveralls.io/repos/github/kmjbyrne/flask-atomic/badge.svg?branch=master)](https://coveralls.io/github/kmjbyrne/flask-atomic?branch=master)


## Introduction

REST API development should be quick and painless, especially when prototyping
or working with large amounts of models where boilerplate CRUD operations are
required. With well-defined code, Flask Atomic has the opportunity to render
redundant ~500 lines of per code, per every 5 models in a project.

This project was heavily influenced by repetitive efforts to get quick and dirty
APIs up and running, with the bad practice of re-using a lot of code, over and over
again. Instead of relying on throwaway efforts, Flask Atomic provides a very
simply means to abstract away hundreds of lines of code and enable RESTful API best
practices that are often esoteric and difficult to engineer for small projects.

Not only does it enable significant off-shelf functionality, it is thoroughly
tested and battle-hardened for development needs.

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

## Installation

`pip install Flask-Atomic`

## Minimal Usage

TODO

