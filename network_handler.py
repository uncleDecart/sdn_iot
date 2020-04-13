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





class SingleSwitchTopo(Topo):
  "Single switch connected to n hosts."
  def build(self, n=2):
    switch = self.addSwitch('s1')
    for h in range(n):
      host = self.addHost('h%s' % (h + 1))
      self.addLink(host, switch)

setLogLevel('info')
print "Create and test a simple network"
#topo = SingleSwitchTopo(n=4)
net = Mininet(switch=OVSSwitch, controller=RemoteController)
c1 = RemoteController('c1', ip='127.0.0.1', port=6653)
net.addController(c1)

info('*** Adicionando os switches\n')
s1 = net.addSwitch('s1', OVSSwitch)
s2 = net.addSwitch('s2', OVSSwitch)
s3 = net.addSwitch('s3', OVSSwitch)
s4 = net.addSwitch('s4', OVSSwitch)

info('*** Adicionando hosts\n')
h1 = net.addHost('h1', mac='1e:0b:fa:73:69:f1')
h2 = net.addHost('h2', mac='1e:0b:fa:73:69:f2')

info('*** Adicionando Links\n')
net.addLink(h1, s1)
net.addLink(s1, s2) # Fluxo 1
net.addLink(s2, s4) # Fluxo 1
net.addLink(s1, s4) # Fluxo 2
net.addLink(s1, s3) # Fluxo 3
net.addLink(s3, s4) # Fluxo 3
net.addLink(h2, s4)

info('*** Iniciando a Rede\n')
net.build()

info('*** Iniciando o Controlador\n')
#c1.start()

info('*** Iniciando os switches\n')
s1.start([c1])
s2.start([c1])
s3.start([c1])
s4.start([c1])

net.start()
#print "Dumping host connections"
#dumpNodeConnections(net.hosts)
#print "Testing network connectivity"
#net.pingAll()
#net.stop()
#global_switch = net.get('s1')
#global_switch.cmd('ovs-vsctl set Bridge s1 protocols=OpenFlow13')
#print "OLOLOLOLOLO"

global_controller = net.get('c1')
global_controller.cmd('ovs-vsctl set Bridge s1 protocols=OpenFlow13')
global_controller.cmd('ryu-manager --observe-links --wsapi-host 0.0.0.0 --wsapi-port 5555 ryu.app.gui_topology.gui_topology')
#global_controller.cmd('ryu-manager --wsapi-host 0.0.0.0 --wsapi-port 5555 --observe-links ryu.app.iot_switch')
