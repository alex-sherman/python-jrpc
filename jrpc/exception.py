import sys

def _get_closest_exception(inheritance_list):
    for except_type in inheritance_list:
        if hasattr(sys.modules["__main__"].__builtins__, except_type["class"]):
            closest_exception = getattr(sys.modules["__main__"].__builtins__, except_type["class"])
            if issubclass(closest_exception, BaseException):
              return closest_exception
    return None


def _getInheritanceList(exception):
    base = exception.__class__
    inheritance = [{"module":base.__module__, "class":base.__name__}]
    
    while base != BaseException:
        base = base.__bases__[0]
        inheritance.append({"module":base.__module__, "class":base.__name__})
    return inheritance

def exception_to_error(exception):
    code = JRPCError.base_exception_code
    return {"code": code, "message": str(exception), "data": {"classes": _getInheritanceList(exception), "args": exception.args}}

class JRPCError(Exception):
    base_exception_code = -32000

    @staticmethod
    def from_error(error):
        code = error["code"]
        msg = error["message"]
        if "data" in error:
            data = error["data"]
        else:
            data = None
        if code in JRPCError.error_codes:
            return JRPCError.error_codes[code](msg, code, data)
        elif code <= -32000 and code >= -32099:
            if code == JRPCError.base_exception_code:
                if data != None and "classes" in data and "args" in data:
                    exceptType = _get_closest_exception(data["classes"])
                    if exceptType != None:
                        return exceptType(*data["args"])
            return ServerError(msg, code, data)
        
        return JRPCError(msg, code, data)
        
    def __init__(self, msg, code = 0, data = None):
        self.code = code
        self.data = data
        Exception.__init__(self, msg)

class ParseError(JRPCError):
    pass

class InvalidRequest(JRPCError):
    pass

class MethodNotFound(JRPCError):
    pass

class InvalidParams(JRPCError):
    pass

class InternalError(JRPCError):
    pass

class ServerError(JRPCError):
    pass

class ClientError(JRPCError):
    pass

JRPCError.error_codes = {-32700: ParseError, -32600: InvalidRequest,
                             -32601: MethodNotFound, -32602: InvalidParams,
                             -32603: InternalError}

