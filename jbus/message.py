import struct
import json
import exception
import socket

def deserialize(s):
    if s.type == socket.SOCK_STREAM:
        return __deserializeTCP(s)
    if s.type == socket.SOCK_DGRAM:
        return __deserializeUDP(s)
def __deserializeTCP(s):
    buf = s.recv(4)
    if not buf: raise exception.MessageException("Client disconnected")
    size, = struct.unpack("!I", buf)
    try:
        json_str = s.recv(size)
        return Message(json.loads(json_str))
    except:
        raise exception.MessageException("Invalid message")
def __deserializeUDP(s):
    buf = s.recv(1500)
    if not buf: raise exception.MessageException("Client disconnected")
    size, = struct.unpack("!I", buf[:4])
    try:
        json_str = buf[4:size + 4]
        return Message(json.loads(json_str))
    except:
        raise exception.MessageException("Invalid message")

def fromdata(buf):
    size, = struct.unpack("!I", buf[:4])
    try:
        json_str = buf[4:4 + size]
        return Message(json.loads(json_str))
    except:
        raise exception.MessageException("Invalid message")

class Message(object):
    def __init__(self, obj = None):
        self.obj = obj
        
    def serialize(self, s):
        s.sendall(self.todata())

    def todata(self):
        json_str = json.dumps(self.obj)
        size = len(json_str)
        return struct.pack("!I{0}s".format(size), size, json_str)

    def __str__(self):
        return json.dumps(self.obj)

    def __getattr__(self, name):
        if not name in self.obj:
            AttributeError
        return self.obj[name]
