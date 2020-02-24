class DataBuffer:

    def __init__(self, data, schema, fields, rels, excs=set()):
        self.object = True
        self.relationships = rels
        if isinstance(data, list):
            self.object = False
        self.schema = schema
        self.data = data
        self.exclusions = excs
        self.base = ''
        self.fields = fields
        self.include = list(map(lambda sch: sch.get('key'), self.schema))

    def hrefbase(self, base):
        self.base = base

    def __getitem__(self, idx):
        if idx > len(self.data):
            raise IndexError('Index exceeds DataBuffer list boundary')
        return self.data[idx]

    def __dict__(self):
        return dict(data=self.json(), schema=self.schema())

    def schema(self):
        return self.schema

    def name(self):
        return str(self.data)

    def showrefs(self, value=True):
        """
        Set the model references value. References are backref and relationships on Alchemy model instances
        :param value: boolean True / False
        :return: self
        :rtype: DataBuffer
        """

        self.relationships = value
        return self

    def prepare(self, instance, exclude):
        if not exclude:
            exclude = []
        if isinstance(instance, tuple):
            return instance[0].serialize(
                rels=self.relationships,
                fields=self.fields,
                exclude=self.exclusions
            )
        return instance.serialize(
            rels=self.relationships,
            fields=self.fields,
            exclude=self.exclusions
        )

    def json(self, exclude=None, relations=None):
        if not exclude:
            exclude = list()
        elif exclude and not hasattr(exclude, '__iter__'):
            raise ValueError('Cannot use exclusions that are not in a collection')

        # exclude = exclude + [self.exclusions]
        # if relations is not None:
        #     self.relationships = relations

        if self.data is None:
            return list()

        if not isinstance(self.data, list):
            instance = self.prepare(self.data, self.fields)
            instance['_href'] = '{}/{}'.format(self.base, self.data.id)
            return instance

        resp = []
        for entry in self.data:
            json = self.prepare(entry, self.fields)
            json['_href'] = '{}/{}'.format(self.base, entry.id)
            resp.append(json)
        return resp

    def view(self):
        return self.data

    def __iter__(self):
        return iter(self.data)

    def __str__(self):
        return dict(data=self.json())
