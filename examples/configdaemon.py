#!/usr/bin/python2.7
import jrpc
import re
from logging import Logger

class DaemonException(Exception):
    pass

class ConfigDaemon(jrpc.service.SocketObject):
    def __init__(self):
        jrpc.service.SocketObject.__init__(self, 50002, debug = True)
        self.settings = {}
        self.settings["somevalue"] = ("somevalue\\s=\\s", "example_config")
        self.settings["anothervalue"] = ("anothervalue\\s=\\s", "example_config")
        self.log.msg("Daemon Started")

    @jrpc.service.method
    def setValue(self, name, value):
        if name not in self.settings:
            raise KeyError("Could not find setting {0}".format(name))
        regex = self.settings[name][0]
        path = self.settings[name][1]
        regex = r"[#\s]*?({0}[\s'\"]*)(.*?)(['\"]*?[;]?[\s]*$)".format(regex)
        lines = []
        with open(path,'r') as f:
            lines = f.readlines()
        if len(lines) == 0: raise SettingException("File {0} is empty".format(path))
        matched = False
        for i in range(len(lines)):
            match = re.match(regex,lines[i])
            if match != None:
                matched = True
                lines[i] = lines[i][match.start(1):match.start(2)] + str(value) + lines[i][match.start(3):match.end(3)+1]
                break
        if not matched: raise SettingException("Setting \"{0}\" could not be found in {1}".format(name, path))
        with open(path,'w') as f:
            f.writelines(lines)
        return value

    @jrpc.service.method
    def getValue(self, name):
        if not name in self.settings:
            raise KeyError("Could not find setting {0}".format(name))
        regex = self.settings[name][0]
        path = self.settings[name][1]
        regex = r"[#\s]*?({0}[\s'\"]*)(.*?)(['\"]*?[;]?[\s]*$)".format(regex)
        lines = []
        with open(path,'r') as f:
            lines = f.readlines()
        for i in range(len(lines)):
            match = re.match(regex,lines[i])
            if match != None:
                return match.group(2)
        raise SettingException("Setting \"{0}\" could not be found in {1}".format(name, path))

    @jrpc.service.method
    def getSettings(self):
        return [key for key, setting in self.settings.iteritems() if setting.local]

    @jrpc.service.method
    def getSettingsInfo(self):
        return {name: {"name": str(prop.name), "type": str(prop.value_type)} for name, prop in self.settings.iteritems() if prop.local}

if __name__ == "__main__":
    daemon = ConfigDaemon()
    daemon.run_wait()