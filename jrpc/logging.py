import inspect
import datetime

class Logger:
    def __init__(self, debug, path = None):
        self.debug = debug
        self.path = path
        self.file = None
        if self.path:
            try:
                self.file = open(self.path, 'a')
            except:
                self.info("Failed to open file for writing: " + self.path)

    def __msg(self, frame, back, level, msg):
        f = frame
        for i in range(back):
            f = f.f_back
        mod = f.f_code.co_filename.split("/")[-1].split("\\")[-1]
        lineno = f.f_lineno
        date = datetime.datetime.now()
        output = str(date) + " " + str(mod) + ":" + str(lineno) + " " + str(level) + " - " + str(msg)
        print output
        if self.file:
            try:
                self.file.write(output + "\n")
                self.file.flush()
            except:
                pass

    def info(self, msg, back = 1):
        if self.debug:
            self.__msg(inspect.currentframe(), back, "INFO", msg)

    def error(self, msg, back = 1):
        self.__msg(inspect.currentframe(), back, "ERROR", msg)

    def msg(self, msg, back = 1):
        self.__msg(inspect.currentframe(), back, "MSG", msg)
