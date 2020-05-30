import os

from webob.static import DirectoryApp

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager

import mysql.connector

from rest import Dispatcher
import bottle
from bottle import response

from mininet.node import OVSSwitch
from bottle import Bottle, request, response
import time
import json
import mysql.connector
import requests
import datetime
import os

from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import OVSController, RemoteController
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch, OVSSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from mininet.term import makeTerm

class EnableCors(object):
  name = 'enable_cors'
  api = 2

  def apply(self, fn, context):
    def _enable_cors(*args, **kwargs):
      # set CORS headers
      response.headers['Access-Control-Allow-Origin'] = '*'
      response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, PUT, OPTIONS'
      response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

      if bottle.request.method != 'OPTIONS':
        # actual request; reply with the actual response
        return fn(*args, **kwargs)

    return _enable_cors

root = Dispatcher()
root.install(EnableCors())
bottle.debug(True)
bottle.install(EnableCors())
bottle.run(app=root, host='0.0.0.0', port=5556)

