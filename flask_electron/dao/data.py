class DataBuffer:

    def __init__(self, data, schema, rel=True, exclusions=None):
        self.object = True
        self.relationships = rel
        self.showrefs(rel)
        if isinstance(data, list):
            self.object = False
        self.schema = schema
        self.data = data
        self.exclusions = exclusions or list()
        self.include = list(map(lambda sch: sch.get('key'), self.schema))

    def name(self):
        return self.data.__repr__()

    def showrefs(self, value=True):
        """
        Set the model references value. References are backref and relationships on Alchemy model instances
        :param value: boolean True / False
        :return: self
        :rtype: DataBuffer
        """

        self.relationships = value
        return self

    def __instance_prep(self, instance, exclude):
        if not exclude:
            exclude = []
        return instance.prepare(
            rel=self.relationships,
            exc=exclude
        )

    def json(self, exclude=None):
        if not exclude:
            exclude = list()
        elif exclude and not hasattr(exclude, '__iter__'):
            raise ValueError('Cannot use exclusions that are not in a collection')

        exclude = exclude + self.exclusions

        if self.data is None:
            return list()

        if self.object:
            return self.__instance_prep(self.data, exclude)
        return [self.__instance_prep(entry, exclude) for entry in self.data]

    def view(self):
        return self.data

    def __iter__(self):
        return iter(self.data)
