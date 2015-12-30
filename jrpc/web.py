from flask import Blueprint, render_template
from service import method, RemoteObject

def EndpointWrapper(method):
    def Wrapped(*args, **kwargs):
        return method(*args, **kwargs), 200
    return Wrapped

class JRPCBlueprint(Blueprint, RemoteObject):
    def __init__(self, *args, **kwargs):
        Blueprint.__init__(self, *args, **kwargs)
        RemoteObject.__init__(self)
        for name, meth in self._get_methods().iteritems():
            url = '/'+name
            if hasattr(meth, 'path'):
                url = meth.path
            self.add_url_rule(url, name, EndpointWrapper(meth))
