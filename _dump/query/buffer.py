from copy import deepcopy

from flask import request
from flask_sqlalchemy import BaseQuery
from flask_atomic.orm.base import DeclarativeBase
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import load_only
from sqlalchemy import desc

from .processor import QueryStringProcessor
from ..orm.helpers import serialize
from ..orm.helpers import relationships
from ..orm.helpers import columns
from ..http.exceptions import HTTPNotFound
from ..http.exceptions import HTTPBadRequest


class QueryBuffer:
    ACCEPTED_CALLS = ['all', 'count']

    def __init__(self, model, queryargs=None, auto=True):
        if not queryargs:
            queryargs = QueryStringProcessor(dict(request.args))
        self.basequery: BaseQuery = model.query
        self._basequery: BaseQuery = model.query
        self.pagedquery = None
        self.queryargs: QueryStringProcessor = queryargs
        self.data: [list, DeclarativeBase] = list()
        self.fields: set = set()
        self.count: int = 0
        self.flags = ['Y']
        self.paginated = False
        self.model = model

        if auto:
            self.apply()

    def json(self, autodata=True, private=False):
        resp = []
        if not autodata:
            for item in self.data:
                resp.append(item.serialize(self.fields, rels=self.queryargs.rels, private=private))
            return resp

        if isinstance(self.data, list):
            for item in self.data:
                resp.append(item.serialize(self.fields, rels=self.queryargs.rels, private=private))
        else:
            return dict(data=self.data.serialize(self.fields, rels=self.queryargs.rels, private=private))
        return dict(data=resp, count=self.count)

    def check_key(self, key: str) -> bool:
        _key = key.split('.')

        for item in self.model.relationattrs():
            try:
                if _key[0] in [i.name for i in getattr(self.model, item).prop.target.columns]:
                    return True
            except Exception:
                continue
        return _key[0] in self.model.relationattrs()

    def apply(self, pending=False, inactive=False):
        entity = self.basequery._entity_zero()
        base_fields = set(map(lambda x: x.key, entity.column_attrs))
        relationships = set(map(lambda x: x.key, entity.relationships))
        keys = columns(self.model, strformat=True)

        self.fields = base_fields.difference(set(self.queryargs.exclusions))
        # Now detect whether we want relationships
        if self.queryargs.include:
            fields = set()
            for item in self.queryargs.include:
                if item not in base_fields:
                    raise HTTPBadRequest('{} is not a recognised attribute of this resource'.format(item))
                fields.add(item)
            self.fields = fields

        if self.queryargs.rels:
            if type(self.queryargs.rels) in [list, set]:
                self.fields.union(set(self.model.relationattrs()).difference(self.queryargs.rels))
            elif self.queryargs.rels:
                self.fields.union(relationships)
                self.queryargs.rels = relationships

        updated_rels = set()

        if type(self.queryargs.rels) in [list, set]:
            for item in self.queryargs.rels:
                if self.check_key(item):
                    pass
                updated_rels.add(item)

        self.queryargs.rels = updated_rels

        if not self.queryargs.sortkey or self.queryargs.sortkey == '':
            self.queryargs.sortkey = entity.primary_key[0].name

        if self.queryargs.sortkey in keys:
            column = getattr(self.basequery._entity_zero().attrs, self.queryargs.sortkey)
            if self.queryargs.descending and self.queryargs.sortkey in self.model.keys():
                self.basequery = self.basequery.order_by(desc(column))
            else:
                self.basequery = self.basequery.order_by(column)

        filters = self.queryargs.filters
        self.basequery, filters = self.check_relationship_filtering(self.basequery, filters)

        # filters = tuple(filter(lambda k: '.' not in k, filters.keys()))

        if 'active' in keys:
            if pending:
                self.flags.append('P')
            if inactive:
                self.flags.append('N')
            self.basequery = self.set_active_filter(self.basequery, self.flags)

        try:
            self.basequery = self.basequery.filter_by(**filters)
        except InvalidRequestError as exc:
            raise HTTPBadRequest(str(exc))

        for key, value in self.queryargs.max:
            self.basequery = self.basequery.filter(getattr(self.model, key) <= value)

        if self.queryargs.page:
            self.pagedquery = self.basequery.paginate(self.queryargs.page, self.queryargs.pagesize or 50, False)
            self.paginated = True
            return self

        self.basequery = self.basequery.group_by(self.model.id)
        self.basequery = self.basequery.limit(self.queryargs.limit)
        self.basequery = self.basequery.options(load_only(*self.fields))
        return self

    def set_active_filter(self, query, flags):
        new_query = query
        if 'active' in self.model.keys() and self.model.active:
            new_query = query.filter(self.model.active.in_(flags))
        return new_query

    def check_relationship_filtering(self, query, filters):
        _filters = filters.copy()
        for item in filters.keys():
            splitter = item.split('.')
            if len(splitter) == 2:
                attribute = getattr(self.model, splitter[0]).comparator.entity.class_
                query = query.join(attribute).filter(getattr(attribute, splitter[1]) == filters[item])
                del _filters[item]
        return query, _filters

    def all(self):
        if self.paginated:
            self.data = self.pagedquery.items
            self.count = getattr(self.basequery, 'count')()
            return self
            # raise ValueError('Cannot run all on a paginated query object')
        self.data = self.basequery.all()
        self.count = len(self.data)
        return self

    def one(self, field, value):
        filter_expression = {field: value}
        query = self.model.query.filter_by(**filter_expression)
        self.data = query.first()
        if not self.data:
            raise HTTPNotFound(f'{str(self.model.__dict__.get("__tablename__"))} not found!')
        for item in relationships(self.model):
            if isinstance(getattr(self.data, item), BaseQuery):
                query = getattr(self.data, item)
                related = QueryBuffer(query, deepcopy(self.queryargs), query._entity_zero().class_)
                related.basequery = related.set_active_filter(related.basequery, self.flags)
                related.fields = related.model.keys().difference(set(self.queryargs.exclusions))
                related_query_data = related.apply().all()
                setattr(self.data, '__i__' + item, related_query_data.json(autodata=False))
        return self

