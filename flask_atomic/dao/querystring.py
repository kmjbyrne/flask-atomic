QUERYSTRING_ARGUMENT_MAP = {
    'true': True,
    'false': False,
    'default': None
}


class QueryStringProcessor:

    def __init__(self, querystring):
        self.querystring = querystring
        self.exclusions = list()
        self.filters = dict()
        self.sortkey = str()
        self.descending = False
        self.__process_querystring()

    def __process_querystring(self):
        for key, value in self.querystring.items():
            if QUERYSTRING_ARGUMENT_MAP.get(value) is False:
                self.exclusions.append(key)
            # Then this value filter is enabled
            self.filters[key] = value

        rels = self.querystring.get('relationships', True)
        if rels:
            self.rels = rels not in ['false', 'N', 'no', 'No', '0']

        order = self.querystring.get('order_by', False)
        if order:
            self.sortkey = order

        descending = self.querystring.get('descending', False)
        if descending:
            self.descending = QUERYSTRING_ARGUMENT_MAP.get(descending, None)
        return self.exclusions
