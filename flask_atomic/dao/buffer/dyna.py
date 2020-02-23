from flask_atomic.dao.buffer.data import DataBuffer


class DYNADataBuffer(DataBuffer):

    def __init__(self, data, schema, fields, rels, *args, **kwargs):
        super().__init__(data, schema, fields, rels, *args, **kwargs)

    def __iter__(self):
        return iter(self.json())

    def show_soft_deletes(self):
        self.vflag = True
        return self

    def prepare_filters(self):
        if not self.filters:
            filters = {}
            filters.update(active='Y')
            self.filters = filters
        if self.vflag and self.filters.get('active', None):
            del self.filters['active']
        self.query = self.query.filter_by(**self.filters)
