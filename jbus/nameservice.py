import threading, socket
import json
import struct

class NameServiceResponder(threading.Thread):
    def __init__(self, service_obj, log):
        threading.Thread.__init__(self)
        self.service_obj = service_obj
        self.log = log
        self.running = True
        self.s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
        self.s.bind(('', 50007))

    def run(self):
        while self.running:
            try:
                data, addr = self.s.recvfrom(1500)
                sport, dport = struct.unpack("!HH", data[20:24])
                print data[28:], self.service_obj.service_name, data[28:] == self.service_obj.service_name
                print dport, sport
                addr = (addr[0], sport)
                
                if dport == 50007 and data[28:] == self.service_obj.service_name:
                    self.log.info("Got request for this service from {0}".format(addr))
                    json_str = json.dumps(self.service_obj.port)
                    tosend = struct.pack("!HHHH{0}s".format(len(json_str)),dport,sport,len(json_str),0,json_str)
                    print tosend
                    self.s.sendto(tosend, addr)
            except socket.timeout:
                continue
            except Exception as e:
                self.log.error("Name service error: {0}".format(e))
                self.close()

    def close(self):
        self.running = False
        self.service_obj.close()
        self.s.close()
