#!/usr/bin/python2.7
import jrpc
import sys

if len(sys.argv) > 1 and len(sys.argv) < 4:
  config_daemon = jrpc.service.SocketProxy(50002)
  try:
    if len(sys.argv) == 2:
      print config_daemon.getValue(sys.argv[1])
      exit()
    if len(sys.argv) == 3:
      print config_daemon.setValue(sys.argv[1], sys.argv[2])
  except Exception as e:
    print type(e), e
  finally:
    config_daemon.close()
    exit()
else:
  print "Usage: configclient.py <setting name> [new value]"
