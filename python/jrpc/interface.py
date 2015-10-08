import inspect
import jrpc

def method(*types):
    def decorator(jrpcMethod):
        jrpcMethod.arguments = zip(inspect.getargspec(jrpcMethod.remote_func)[0][1:], types)
        return jrpcMethod
    return decorator

def InterfaceObject(remoteObject):
    @jrpc.service.method
    def GetInterface(self):
        interfaces = {}
        methods = {}
        types = {}
        for name, jrpc_object in self.jrpc_objects.iteritems():
            if isinstance(jrpc_object, jrpc.service.RemoteObject) and hasattr(jrpc_object, "GetInterface"):
                interfaces[name] = jrpc_object.GetInterface()
            if isinstance(jrpc_object, jrpc.service.method) and hasattr(jrpc_object, "arguments"):
                methods[name] = InterfaceType.ToDict(jrpc_object.arguments)
                types.update(InterfaceType.ToTypeDef(jrpc_object.arguments))
        return {
            "types": types,
            "methods": methods,
            "interfaces": interfaces
        }
    remoteObject.GetInterface = GetInterface
    return remoteObject

class InterfaceType(object):
    @staticmethod
    def GetClassMembers(Class):
        return dict([item for item in inspect.getmembers(Class)
                if isinstance(item[1], InterfaceType)])

    @staticmethod
    def ToDict(members):
        if(isinstance(members, dict)):
            return dict([(attribute[0], attribute[1].toDict()) for attribute in members.iteritems()])
        if(isinstance(members, list)):
            return [(attribute[0], attribute[1].toDict()) for attribute in members]

    @staticmethod
    def ToTypeDef(members):
        output = {}
        if(isinstance(members, list)):
            members = dict(members)
        for attribute in members.values():
            typeDef = attribute.toTypeDef(output)
        return output


    def __init__(self):
        self.type = self.__class__.__name__
        boring = dir(type(self.type, (object,), {}))
        self.members = InterfaceType.GetClassMembers(self.__class__)
        self.parameters = {}
        self._inited = True

    def __setattr__(self, name, value):
        if(not hasattr(self, "_inited")):
            super(InterfaceType, self).__setattr__(name, value)
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
            return
        selfType = {}
        if len(self.members):
            selfType["members"] = dict([(name, attr.toDict()) for name, attr in self.members.iteritems()])
        typeDef[self.type] = selfType
        for attribute in self.members.values():
            attribute.toTypeDef(typeDef)
        return typeDef

class NUMBER(InterfaceType):
    def __init__(self, vmin = None, vmax = None):
        InterfaceType.__init__(self)
        if vmin != None:
            self.min = vmin
        if vmax != None:
            self.max = vmax

class STRING(InterfaceType):
    def __init__(self,):
        InterfaceType.__init__(self)

PRIMITIVES = [NUMBER, STRING]