class ServiceException(Exception):
    def __init__(self, msg, inner_exception_type = None):
        self.inner_exception_type = inner_exception_type
        Exception.__init__(self, msg)

class MessageException(ServiceException):
    pass

class MethodException(ServiceException):
    pass
