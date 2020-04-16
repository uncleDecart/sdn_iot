#!/usr/bin/python
from bottle import Bottle, request
import time

class Dispatcher(Bottle):
  def __init__(self, net):
    super(Dispatcher, self).__init__()
    self.net = net
    self.route('/nodes/<node_name>', method='POST', callback=self.post_node)
    self.route('/switch/add/<switch_name', method='POST', callback=self.add_switch)
    self.route('/nodes/<node_name>/cmd', method='POST', callback=self.do_cmd)

  def post_node(self, node_name):
    node = self.net[node_name]
    node.params.update(request.json['params'])

  def add_switch(self, switch_name):
    if not self.net[switch_name]:
      s = self.net.AddSwitch(switch_name)
      s.params.update(request.json['params'])
    else:
      bottle.response.status = 403

  def add_link(self, node_a, node_b):
    a = self.net[node_a]
    b = self.net[node_b]
    if not a or not b:
      bottle.response.status = 403
    else:
      self.net.addLink(a, b)

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
