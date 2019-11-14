
class DataBuffer:

    def __init__(self, data, schema, exclusions):
        self.object = True
        self.relationships = True
        if isinstance(data, list):
            self.object = False
        self.schema = schema
        self.data = data
        self.exclusions = exclusions
        self.include = list(map(lambda sch: sch.get('key'), self.schema))

    def showrefs(self, value=True):
        """
        Set the model references value. References are backref and relationships on Alchemy model instances
        :param value: boolean True / False
        :return: self
        :rtype: DataBuffer
        """

        self.relationships = value
        return self

    def _instance_prep(self, instance, exclude):
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
        if self.object:
            return self._instance_prep(self.data, exclude)
        return [self._instance_prep(entry, exclude) for entry in self.data]

    def view(self):
        return self.data

    def __iter__(self):
        return iter(self.data)