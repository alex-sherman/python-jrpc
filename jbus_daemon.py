import jbus
import inspect

class Daemon(jbus.service.Object):
    
    def __init__(self, debug = False):
        jbus.service.Object.__init__(self, "JBUS-Daemon", debug)
        self.port = 50007
        self.registered = True
        self.known_services = {}
        
    @jbus.service.method
    def get_service(self, service_name):
        return self.known_services[service_name]

    @jbus.service.method
    def register_service(self, service_name, port):
        self.known_services[service_name] = port



if __name__ == "__main__":
    daemon = Daemon(True)
    daemon.run_wait()
