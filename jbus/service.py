import threading
import socket
import logging
import time
import exception
import json

class Object(threading.Thread):
    def __init__(self, service_name, debug = False):
        threading.Thread.__init__(self)
        self.log = logging.Logger(debug)
        self.running = True
        self.service_name = service_name
        self.daemon_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.registered = False
        socket.setdefaulttimeout(1)

    def run_wait(self):
        self.start()
        try:
            while self.running:
                time.sleep(1)
        except:
            self.close()
    def run(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('', 50007))
        self.s.listen(1)
        self.log.info("Service listening")
        while self.running:
            try:
                conn, addr = self.s.accept()
                self.log.info("Got connection from {0}".format(addr))
                responder = ServiceResponder(conn, addr, self.log)
                responder.start()
            except socket.timeout:
                continue
            except Exception:
                self.close()
            
    def close(self):
        if not self.running: return
        self.running = False
        if self.s != None:
            self.log.info("Closing socket")
            self.s.close()
            del self.s

class ServiceResponder(threading.Thread):
    def __init__(self, socket, addr, log):
        threading.Thread.__init__(self)
        self.socket = socket
        self.addr = addr
        self.log = log
        self.running = True
    def run(self):
        while self.running:
            try:
                msg = self.socket.recv(1024)
                print json.loads(msg)
            except socket.timeout:
                continue
            except Exception as e:
                self.log.info("Client socket exception: {0}".format(e))
                self.close()
    def close(self):
        if not self.running: return
        self.running = False
        if self.socket != None:
            self.log.info("Client disconnected {0}".format(self.addr))
            self.socket.close()
            del self.socket

class Proxy(object):
    def __init__(self, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', port))
        except Exception as e:
            raise exception.ServiceException("Failed to connected to service", e)

    def herp(self):
        self.socket.sendall(json.dumps({"what": "ok"}))
        
        
