import os

from webob.static import DirectoryApp


from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager

from mininet.topo import Topo
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

import mysql.connector

from rest import Dispatcher
import bottle
from bottle import response

CONTROLLER_HOST = '0.0.0.0'
CONTROLLER_PORT = '5555'
CONTROLLER_URI = 'http://{}:{}/'.format(CONTROLLER_HOST, CONTROLLER_PORT)

switch_list = ['s1', 's2', 's3', 's4']

class MyTopo( Topo ):
  "Simple topology example."

  def build( self ):
    h1 = self.addHost('h1')
    h2 = self.addHost('h2')

    s1 = self.addSwitch('s1')
    s2 = self.addSwitch('s2')
    s3 = self.addSwitch('s3')
    s4 = self.addSwitch('s4')

    self.addLink(h1, s1)
    self.addLink(s1, s2)
    self.addLink(s2, s4)
    self.addLink(s1, s4)
    self.addLink(s1, s3)
    self.addLink(s3, s4)
    self.addLink(h2, s4)

setLogLevel('debug')
topo = MyTopo()
net = Mininet(topo, switch=OVSSwitch, controller=RemoteController('c0', ip='127.0.0.1', port=6653))

for sn in switch_list:
  s = net[sn]
  s.cmd('ovs-vsctl set Bridge %s protocols=OpenFlow13' % sn)

#net.build()

ryu_cmd = "ryu-manager --observe-links --wsapi-host %s --wsapi-port %s ryu.app.simple_switch_13 &" % (CONTROLLER_HOST, CONTROLLER_PORT)
c0 = net['c0']
#ryu_cmd = "ryu-manager --observe-links ryu.app.simple_switch_13 &"
c0.cmd(ryu_cmd)

net.start()
#net.pingAll()

#c1.start()

#CLI(net)

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

root = Dispatcher(net, switch_list)
root.install(EnableCors())
bottle.debug(True)
bottle.install(EnableCors())
bottle.run(app=root, host='0.0.0.0', port=5556)

net.stop()

