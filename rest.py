#!/usr/bin/python
from mininet.node import OVSSwitch
from bottle import Bottle, request
import time

class Dispatcher(Bottle):
  def __init__(self, net, sl):
    super(Dispatcher, self).__init__()
    self.net = net
    self.switch_list = sl[:]
    self.route('/nodes/<node_name>', method='POST', callback=self.post_node)
    self.route('/switch/add/<switch_name>', method='POST', callback=self.add_switch)
    self.route('/link/add', method='GET', callback=self.add_link)
    self.route('/test', method='GET', callback=self.test)
    self.route('/nodes/<node_name>/cmd', method='POST', callback=self.do_cmd)


  def test(self):
    return "TEST!"

  def post_node(self, node_name):
    node = self.net[node_name]
    node.params.update(request.json['params'])

  def add_switch(self, switch_name):
    if switch_name not in self.switch_list:
      c1 = self.net.get('c1')
      s = self.net.addSwitch(switch_name, OVSSwitch)
      s.params.update(request.json['params'])
      #self.net.addLink(self.net.get('s1'), s)
      s.start([c1])
      c1.cmd('ovs-vsctl set Bridge %s protocols=OpenFlow13' % switch_name)
      self.switch_list.append(switch_name)
    else:
      bottle.response.status = 403

  def add_link(self):
    a = request.query.a
    b = request.query.b
    if a not in self.switch_list or b not in self.switch_list:
      bottle.response.status = 403
    else:
      self.net.addLink(self.net.get(a), self.net.get(b))

  def do_cmd(self, node_name):
    args = request.body.read()
    node = self.net[node_name]
    rest = args.split(' ')
    # Substitute IP addresses for node names in command
    # If updateIP() returns None, then use node name
    rest = [self.net[arg].defaultIntf().updateIP() or arg if arg in self.net else arg for arg in rest]
    rest = ' '.join(rest)
    # Run cmd on node:
    node.sendCmd(rest)
    output = ''
    init_time = time.time()
    while node.waiting:
      exec_time = time.time() - init_time
      #timeout of 5 seconds
      if exec_time > 5:
        break
      data = node.monitor(timeoutms=1000)
      output += data
    # Force process to stop if not stopped in timeout
    if node.waiting:
      node.sendInt()
      time.sleep(0.5)
      data = node.monitor(timeoutms=1000)
      output += data
      node.waiting = False
    return output
