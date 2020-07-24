QUERYSTRING_ARGUMENT_MAP = {
    'true': True,
    'false': False,
    'default': None
}

QUERYSTRING_CONTROL_KEYS = [
    'exclude',
    'limit', 'page',
    'order_by', 'desc',
    'min', 'max', 'only',
    'count', 'pagesize',
    'page', 'only'
]


class QueryStringProcessor:

    def __init__(self, querystring):
        self.querystring = querystring
        self.exclusions = list()
        self.filters = dict()
        self.namefilters = tuple()
        self.sortkey = str()
        self.limit = 100
        self.rels = False
        self.min = list()
        self.max = list()
        self.include = set()
        self.counts = {}
        self.descending = False
        self.page = None
        self.pagesize = 50
        self.__process_querystring()

    def splitspecial(self, key, operand):
        unpacked = key.split(operand)
        return (unpacked.pop(0), unpacked.pop())

    def __process_querystring(self):
        if not self.querystring:
            return None

        filterkeys = filter(
            lambda i: i[0] != 'relationships' and i[0] not in QUERYSTRING_CONTROL_KEYS, self.querystring.items()
        )
        for key, value in filterkeys:
            if '>' in key:
                _key, _value = self.splitspecial(key, '>')
                self.min.append((_key, _value,))
            elif '<' in key:
                _key, _value = self.splitspecial(key, '<')
                self.max.append((_key, _value,))
            elif QUERYSTRING_ARGUMENT_MAP.get(value) is False:
                self.exclusions.append(key)
            else:
                # Then this value filter is enabled
                self.filters[key] = value

        rels = self.querystring.get('relationships', None)
        if rels and rels not in ['false', 'N', 'no', 'No', '0']:
            if QUERYSTRING_ARGUMENT_MAP.get(rels) is not None:
                self.rels = QUERYSTRING_ARGUMENT_MAP.get(rels)
            else:
                self.rels = rels.split(',')

        only = self.querystring.get('only', None)
        if only:
            fields = self.querystring.get('only')

        if self.querystring.get('only', None):
            for field in self.querystring.get('only').split(','):
                self.include.add(field)

        order = self.querystring.get('order_by', False)
        if order:
            self.sortkey = order

        limit = self.querystring.get('limit', False)
        if limit:
            self.limit = int(limit)

        descending = self.querystring.get('desc', False)
        if descending:
            self.descending = QUERYSTRING_ARGUMENT_MAP.get(descending, None)

        pagesize = self.querystring.get('pagesize', False)
        if pagesize:
            self.pagesize = int(pagesize)

        page = self.querystring.get('page', False)
        if page:
            self.page = int(page)

        counts = self.querystring.get('count', None)
        if counts:
            for field in counts.split(','):
                # Like a partial function, call it on the relations when ready
                self.counts[field] = len

        gt = self.querystring.get('gt', False)
        if gt:
            self.gt = gt
