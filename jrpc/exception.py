def _get_closest_exception(exception_type):
    current_tree = JRPCError.exception_tree
    best_guess = None
    while current_tree:
        next_guess = [(guess, next_tree) for guess, next_tree in current_tree.iteritems()
                      if issubclass(exception_type, guess)]
        if len(next_guess) == 0: return best_guess
        best_guess = next_guess[0][0]
        current_tree = next_guess[0][1]
    if best_guess == None: raise Exception("Cannot serialize exception {0}".format(exception))
    return best_guess

def _get_exception_code(exception_type):
    best_guess = _get_closest_exception(exception_type)
    for code, exception_type in JRPCError.base_exception_codes.iteritems():
        if exception_type is best_guess:
            return code
    raise Exception("Missing error code lookup {0}".format(best_guess))

def exception_to_error(exception):
    best_guess = None
    code = _get_exception_code(type(exception))
    return {"code": code, "message": exception.message, "data": str(type(exception))}

class JRPCError(Exception):
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
        if code in JRPCError.base_exception_codes:
            return JRPCError.base_exception_codes[code](msg)
        
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
JRPCError.base_exception_codes = {-32000: BaseException, -32004: Exception, -32006: StandardError, -32008: ArithmeticError,
                                  -32011: ZeroDivisionError, -32013: AttributeError, -32015: IOError}

JRPCError.exception_tree = {
    BaseException:
    {
        Exception:
        {
            StandardError: {
                ArithmeticError: {
                    ZeroDivisionError: {}
                },
                AttributeError: {}
            }
        }
    }
}
