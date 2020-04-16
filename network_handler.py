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
from wsgiproxy.app import WSGIProxyApp
import bottle

CONTROLLER_HOST = '0.0.0.0'
CONTROLLER_PORT = '5555'
CONTROLLER_URI = 'http://{}:{}/'.format(CONTROLLER_HOST, CONTROLLER_PORT)

setLogLevel('info')
print "Create and test a simple network"
#topo = SingleSwitchTopo(n=4)
net = Mininet(switch=OVSSwitch, controller=RemoteController)
c1 = RemoteController('c1', ip='127.0.0.1', port=6653)
net.addController(c1)

s1 = net.addSwitch('s1', OVSSwitch)
s2 = net.addSwitch('s2', OVSSwitch)
s3 = net.addSwitch('s3', OVSSwitch)
s4 = net.addSwitch('s4', OVSSwitch)

h1 = net.addHost('h1', mac='1e:0b:fa:73:69:f1')
h2 = net.addHost('h2', mac='1e:0b:fa:73:69:f2')

net.addLink(h1, s1)
net.addLink(s1, s2)
net.addLink(s2, s4)
net.addLink(s1, s4)
net.addLink(s1, s3)
net.addLink(s3, s4)
net.addLink(h2, s4)

net.build()
s1.start([c1])
s2.start([c1])
s3.start([c1])
s4.start([c1])

global_controller = net.get('c1')
global_controller.cmd('ovs-vsctl set Bridge s1 protocols=OpenFlow13')
ryu_cmd = "ryu-manager --observe-links --wsapi-host %s --wsapi-port %s ryu.app.gui_topology.gui_topology &" % (CONTROLLER_HOST, CONTROLLER_PORT)
global_controller.cmd(ryu_cmd)

net.start()

root = Dispatcher(net)
bottle.debug(True)
bottle.run(app=root, host='0.0.0.0', port=5556)

net.stop()