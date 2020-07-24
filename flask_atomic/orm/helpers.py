from typing import Optional
from datetime import datetime
from datetime import date


def relationships(model):
    return model.__mapper__.relationships


def columns(model, strformat=False, relations=None):
    bound_columns = set(model.__mapper__.columns)
    if relations:
        return bound_columns.union(set([i.class_attribute for i in model.__mapper__.relationships]))
    if strformat:
        return [i.name for i in bound_columns]
    return bound_columns


def getschema(model):
    cols = set([i.name for i in columns(model)])
    cols = cols.difference([i.name for i in getattr(model, 'hidden', [])])
    schemamap = {
        'model': model.__tablename__,
        'fields': []
    }

    for item in cols:
        column = getattr(model, item)
        schemamap['fields'].append(dict(name=column.name, type=str(column.type)))

    return schemamap


def extract(element, fields=None, exclude: Optional[set] = None, **kwargs) -> dict:
    resp = dict()
    if exclude is None:
        exclude = set()

    if fields is None:
        fields = columns(element, strformat=True)

    for column in set(fields).difference(set(exclude)):
        if isinstance(getattr(element, column), datetime) or isinstance(getattr(element, column), date):
            resp[column] = str(getattr(element, column))
        else:
            resp[column] = getattr(element, column)
    return resp


def process_relationship(data, exclude):
    resp = None
    if isinstance(data, list):
        resp = []
        for item in data:
            resp.append(extract(item, columns(item, strformat=True), exclude))
        return resp
    return resp


def serialize(model, data, fields=None, exc: Optional[set] = None, rels=None, root=None, exclude=None, functions=None,
              **kwargs):
    """
    This utility function dynamically converts Alchemy model classes into a
    dict using introspective lookups. This saves on manually mapping each
    model and all the fields. However, exclusions should be noted. Such as
    passwords and protected properties.

    :param model: SQLAlchemy model
    :param data: query data
    :param functions:
    :param fields: More of a whitelist of fields to include (preferred way)
    :param rels: Whether or not to introspect to relationships
    :param exc: Fields to exclude from query result set
    :param root: Root model for processing relationships. This acts as a
    recursive sentinel to prevent infinite recursion due to selecting oneself
    as a related model, and then infinitely trying to traverse the roots
    own relationships, from itself over and over.
    :param exclude: Exclusion in set form. Currently in favour of exc param.

    Only remedy to this is also to use one way relationships. Avoiding any
    back referencing of models.

    :return: json data structure of model
    :rtype: dict
    """

    if functions is None:
        functions = {}
    if exclude is None:
        exclude = set()
    else:
        exclude = set(exclude)

    exclude.update(map(lambda col: col.name, getattr(model, 'hidden', set())))

    if not fields:
        fields = set(columns(model, strformat=True))

    fields = fields.difference(exclude)

    def process(element):
        transformed = extract(element, fields, set(), **kwargs)
        if functions:
            for key, value in functions.items():
                transformed[f'_{key}'] = value(getattr(element, key))
        # rels = set([i.key for i in element.__mapper__.relationships]).intersection(fields)
        if not rels or len(([i.key for i in element.__mapper__.relationships])) < 1:
            return transformed

        for item in rels:
            transformed[item] = process_relationship(getattr(element, item), exclude=exclude)
        return transformed

    if root is None:
        root = model.__tablename__

    # Define our model properties here. Columns and Schema relationships
    if not isinstance(data, list):
        return process(data)
    resp = []
    for element in data:
        resp.append(process(element))
    return resp