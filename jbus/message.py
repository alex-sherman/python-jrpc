import struct
import json
import exception

class Message(object):
    def __init__(self, obj = None):
        self.obj = obj
    def serialize(self, socket):
        json_str = json.dumps(self.obj)
        size = len(json_str)
        socket.sendall(struct.pack("!I{0}s".format(size), size, json_str))
    def deserialize(self, socket):
        buf = socket.recv(4)
        if not buf: raise exception.MessageException("Client disconnected")
        size, = struct.unpack("!I", buf)
        try:
            json_str = socket.recv(size)
            self.obj = json.loads(json_str)
        except:
            return False
        return True
    def __str__(self):
        return json.dumps(self.obj)
