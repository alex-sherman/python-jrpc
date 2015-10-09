import inspect
import jrpc

class RPCType(object):
    """This can be subclassed to specify a custom type to be used with a Remote Object"""

    @staticmethod
    def ToDict(members):
        """Converts an argument list [(name, type), (name, type)...] into a JSON serializble array"""
        return [(attribute[0], attribute[1].toDict()) for attribute in members]

    @staticmethod
    def ToTypeDef(members, typeDef):
        output = {}
        for _, attribute in members:
            output.update(attribute.toTypeDef(typeDef))
        return output


    def __init__(self):
        self.type = self.__class__.__name__
        boring = dir(type(self.type, (object,), {}))
        self.members = dict([item for item in inspect.getmembers(self.__class__)
                if isinstance(item[1], RPCType)])
        self.parameters = {}
        self._inited = True

    def __setattr__(self, name, value):
        if(not hasattr(self, "_inited")):
            super(RPCType, self).__setattr__(name, value)
        else:
            self.parameters[name] = value

    def toDict(self):
        output = {
            "type": self.type
        }
        if self.parameters:
            output["parameters"] = self.parameters
        return output

    def isPrimitive(self):
        return type(self) in PRIMITIVES

    def toTypeDef(self, typeDef):
        if self.type in typeDef or self.isPrimitive():
            return {}
        selfType = {}
        if len(self.members):
            selfType["members"] = dict([(name, attr.toDict()) for name, attr in self.members.iteritems()])
        typeDef[self.type] = selfType
        for attribute in self.members.values():
            attribute.toTypeDef(typeDef)
        return {self.type: selfType}

class UNKNOWN(RPCType):
    pass

class OBJECT(RPCType):
    pass

class NUMBER(RPCType):
    def __init__(self, vmin = None, vmax = None):
        RPCType.__init__(self)
        if vmin != None:
            self.min = vmin
        if vmax != None:
            self.max = vmax

class STRING(RPCType):
    pass

PRIMITIVES = [UNKNOWN, OBJECT, NUMBER, STRING]