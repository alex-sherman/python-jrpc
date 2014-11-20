import threading, socket
import json
import struct
import message

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
                addr = (addr[0], sport)
                if dport == 50007:
                    msg = message.fromdata(data[28:])
                    if hasattr(msg, "procedure") and hasattr(msg, "args") \
                        and msg.procedure == "get_service" and msg.args[0] == self.service_obj.service_name:
                        self.log.info("Got request for this service from {0}".format(addr))
                        response = message.Message({"status": 200, "data": self.service_obj.port})
                        res_str = response.todata()
                        tosend = struct.pack("!HHHH{0}s".format(len(res_str)),dport,sport,len(res_str) + 8,0,res_str)
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
