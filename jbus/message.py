import struct
import json
import exception
import socket

class Message(object):
    def __init__(self, obj = None):
        self.obj = obj
        
    def serialize(self, s):
        s.sendall(self.todata())

    def todata(self):
        json_str = json.dumps(self.obj)
        size = len(json_str)
        return struct.pack("!I{0}s".format(size), size, json_str)

    def fromdata(self, buf):
        size, = struct.unpack("!I", buf[:4])
        try:
            json_str = buf[4:4 + size]
            self.obj = json.loads(json_str)
        except:
            raise exception.MessageException("Invalid message")
        return True
    
    def deserialize(self, s):
        if s.type == socket.SOCK_STREAM:
            return self.__deserializeTCP(s)
        if s.type == socket.SOCK_DGRAM:
            return self.__deserializeUDP(s)
    def __deserializeTCP(self, s):
        buf = s.recv(4)
        if not buf: raise exception.MessageException("Client disconnected")
        size, = struct.unpack("!I", buf)
        try:
            json_str = s.recv(size)
            self.obj = json.loads(json_str)
        except:
            raise exception.MessageException("Invalid message")
        return True
    def __deserializeUDP(self, s):
        buf = s.recv(1500)
        if not buf: raise exception.MessageException("Client disconnected")
        size, = struct.unpack("!I", buf[:4])
        try:
            json_str = buf[4:size + 4]
            self.obj = json.loads(json_str)
        except:
            raise exception.MessageException("Invalid message")
        return True
        
    def __str__(self):
        return json.dumps(self.obj)

    def __getattr__(self, name):
        if not name in self.obj:
            AttributeError
        return self.obj[name]
