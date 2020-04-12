import os

from webob.static import DirectoryApp

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import OVSController, RemoteController

class SingleSwitchTopo(Topo):
  "Single switch connected to n hosts."
  def build(self, n=2):
    switch = self.addSwitch('s1')
    for h in range(n):
      host = self.addHost('h%s' % (h + 1))
      self.addLink(host, switch)

setLogLevel('info')
print "Create and test a simple network"
topo = SingleSwitchTopo(n=4)
net = Mininet(topo, controller=OVSController)
#c0 = RemoteController('c0', ip='127.0.0.1', port=6653)
#net.addController(c0)

net.start()
print "Dumping host connections"
dumpNodeConnections(net.hosts)
#print "Testing network connectivity"
#net.pingAll()
#net.stop()
global_switch = net.get('s1')

global_controller = net.get('c0')
global_controller.cmd('ovs-vsctl set Bridge s1 protocols=OpenFlow13')
global_controller.cmd('ryu-manager --wsapi-host 0.0.0.0 --wsapi-port 5555 --observe-links ryu.app.iot_switch')

