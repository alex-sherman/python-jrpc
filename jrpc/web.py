from flask import Blueprint, render_template
from service import method, RemoteObject
import json

def EndpointWrapper(method):
    def Wrapped(*args, **kwargs):
        return json.dumps(method(*args, **kwargs)), 200
    return Wrapped

class JRPCBlueprint(Blueprint, RemoteObject):
    def __init__(self, *args, **kwargs):
        Blueprint.__init__(self, *args, **kwargs)
        RemoteObject.__init__(self)
        self.registerObjMethods(self)

    def registerObjMethods(self, obj, prefix = '/'):
        for name, meth in obj._get_methods().iteritems():
            url = prefix + name
            if 'path' in meth.options:
                url = prefix + meth.options['path']
            print url, name
            self.add_url_rule(url, url, EndpointWrapper(meth))

        for name, obj in obj._get_objects().iteritems():
            self.registerObjMethods(obj, prefix + name + '/')
