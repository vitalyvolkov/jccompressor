class BaseJCBackend:

    def __init__(self, filetype):
        self.filetype = filetype

    def read(self, stream):
        return stream.read()
