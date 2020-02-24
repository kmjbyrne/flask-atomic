from flask_sqlalchemy import BaseQuery
from sqlalchemy.orm import eagerload
from sqlalchemy.orm import load_only

from flask_atomic.dao.buffer.dyna import DYNADataBuffer


class QueryBuffer:

    def __init__(self, query, model, rel=False, vflag=False, dao=None, queryargs=None):
        self.query = query
        self.model = model
        self._ordered = False
        self.fields = None
        self.filters = None
        self.relationships = False
        self.exclusions = []
        self.vflag = vflag
        self.queryargs = queryargs
        self.prepare_filters()

    def includerels(self, args):
        self.relationships = args

    def exclude(self, exclude):
        self.exclusions = exclude
        fields = self.model.keys()

        include = []
        for item in fields:
            if item not in exclude:
                include.append(item)

        self.query = self.query.options(load_only(*include))
        self.fields = fields
        return self

    def select(self, fields):
        self.fields = self.model.fields(inc=fields)
        self.query = self.query.options(load_only(*fields))
        return self

    def limit(self, count):
        if not isinstance(count, int) or count < 0:
            raise ValueError('Cannot process a non-integer for limit size')
        self.query = self.query.limit(count)
        return self

    def like(self, field, expression):
        self.query = self.query.filter(field.like(expression))
        return self

    def gtdate(self, field, date):
        field = self.model.normalise(field)
        self.query = self.query.filter(getattr(self.model, field) >= date)
        return self

    def ltdate(self, field, date):
        field = self.model.normalise(field)
        self.query = self.query.filter(getattr(self.model, field) <= date)
        return self

    def filter(self, filters, operand='MIN'):
        namedfilters = tuple()
        for named_item in [i for i in filters if i]:
            if operand == 'HAS':
                return self.query.filter(getattr(self.model, named_item[0]) == named_item[1])
            elif operand == 'MIN':
                self.query = self.query.filter(getattr(self.model, named_item[0]) >= named_item[1])
            else:
                namedfilters = namedfilters + (getattr(self.model, named_item[0]) <= named_item[1])
        return self

    def efilter(self, expression_filter):
        self.query = self.query.filter(expression_filter)
        return self

    def filter_by(self, filters):
        if not filters:
            filters = {}
        self.filters = self.model.checkfilters(filters)
        self.prepare_filters()
        return self

    def options(self, relationships=None):
        if not relationships:
            return self
        elif isinstance(relationships, tuple):
            for item in relationships:
                self.query = self.query.options(eagerload(item))
        return self

    def order_by(self, field=None, descending=False):
        if not field:
            return self
        order = self.model.identify_primary_key()
        if field:
            order = field
            self._ordered = True
        if descending:
            self.query = self.query.order_by(getattr(self.model, order).desc())
            return self
        self.query = self.query.order_by(order)
        return self

    def schema(self, schema, fields):
        return list(
            map(
                lambda x: dict(
                    name=' '.join(x.get('key').split('_')).title(),
                    key=x.get('key')
                ), filter(lambda item: item.get('key') in fields, schema)
            )
        )

    def marshall(self, data, schema):
        if not self.fields:
            self.fields = self.model.keys()
        return DYNADataBuffer(data, self.schema(schema, self.fields), self.fields, self.queryargs.rels,
                              self.queryargs.exclusions)

    def autoquery(self):
        self.fields = set(self.model.fields(exc=self.queryargs.exclusions))
        # Now detect whether we want relationships
        if self.queryargs.rels:
            self.fields = self.fields.union(set(self.model.relations(self.queryargs.rels)))
        self.order_by(self.queryargs.sortkey, descending=self.queryargs.descending)
        self.filter([self.queryargs.min], 'MIN')
        self.filter_by(self.queryargs.filters)
        self.limit(self.queryargs.limit)
        self.options(load_only(*self.fields))
        return self

    def execute(self, query: BaseQuery.statement) -> object:
        return query()

    def all(self, *args):
        resp = self.execute(self.query.all)
        return self.marshall(resp, self.model.schema())

    def one(self):
        resp = self.execute(self.query.one)
        return self.marshall(resp, self.model.schema())

    def first(self):
        resp = self.execute(self.query.first)
        return self.marshall(resp, self.model.schema())

    def prepare_filters(self):
        if not self.filters:
            filters = {}
            # filters.update(active='Y')
            self.filters = filters
        if self.vflag and self.filters.get('active', None):
            del self.filters['active']
        self.query = self.query.filter_by(**self.filters)

    def __iter__(self):
        return self.all()
