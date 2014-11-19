class ServiceException(Exception):
    def __init__(self, msg, inner_exception):
        self.inner_exception = inner_exception
        Exception.__init__(self, msg)
