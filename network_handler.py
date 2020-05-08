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

from rest import Dispatcher
import bottle
from bottle import response

CONTROLLER_HOST = '0.0.0.0'
CONTROLLER_PORT = '5555'
CONTROLLER_URI = 'http://{}:{}/'.format(CONTROLLER_HOST, CONTROLLER_PORT)

setLogLevel('info')
print "Create and test a simple network"
#topo = SingleSwitchTopo(n=4)
net = Mininet(switch=OVSSwitch, controller=RemoteController)
c1 = RemoteController('c1', ip='127.0.0.1', port=6653)
net.addController(c1)

switch_list = ['s1', 's2', 's3', 's4']

for sn in switch_list:
  s = net.addSwitch(sn, OVSSwitch)
  s.cmd('ovs-vsctl set Bridge %s protocols=OpenFlow13' % sn)

h1 = net.addHost('h1')

h2 = net.addHost('h2')

s1 = net.get('s1')
s2 = net.get('s2')
s3 = net.get('s3')
s4 = net.get('s4')

net.addLink(h1, s1)
net.addLink(s1, s2)
net.addLink(s2, s4)
net.addLink(s1, s4)
net.addLink(s1, s3)
net.addLink(s3, s4)
net.addLink(h2, s4)

net.build()

#ryu_cmd = "ryu-manager --observe-links --wsapi-host %s --wsapi-port %s ryu.app.simple_switch ryu.app.gui_topology.gui_topology" % (CONTROLLER_HOST, CONTROLLER_PORT)
ryu_cmd = "ryu-manager --observe-links --wsapi-host %s --wsapi-port %s ryu.app.iot_switch &" % (CONTROLLER_HOST, CONTROLLER_PORT)
#print "FUCK ME %s" % c1.cmd(ryu_cmd)
c1.cmd(ryu_cmd)

net.start()
#net.pingAll()

#c1.start()

for sn in switch_list:
  s = net[sn]
  s.start([c1])

CLI(net)

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


