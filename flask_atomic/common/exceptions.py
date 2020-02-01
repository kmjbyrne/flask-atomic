class MissingConfigurationValue(IOError):

    def __init__(self, key=None):
        msg = 'Application requires {}'.format(key)
        super(IOError, self).__init__(msg)
        self.msg = msg
