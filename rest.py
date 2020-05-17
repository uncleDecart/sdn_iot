#!/usr/bin/python
from mininet.node import OVSSwitch
from bottle import Bottle, request, response
import time
import json
import mysql.connector

class Dispatcher(Bottle):
  def __init__(self, net, sl):
    super(Dispatcher, self).__init__()
    config = {
      'user' : 'root',
      'password' : 'root',
      'host' : 'db',
      'port' : '3306',
      'database' : 'emulator'
    }
    self.connection = mysql.connector.connect(**config)
    self.cursor = self.connection.cursor()
    print "SOME SHIT DUDUDUDUDU"
    self.net = net
    self.starting_mac = 0x1E0BFA737000 # 1E:0B:FA:73:70:00
    self.switch_list = sl[:]
    self.route('/nodes/<node_name>', method='POST', callback=self.post_node)
    self.route('/switch/<switch_name>', method='POST', callback=self.add_switch)
    self.route('/switch/<switch_name>', method='DELETE', callback=self.del_switch)
    self.route('/link', method='POST', callback=self.add_link)
    self.route('/link', method='DELETE', callback=self.del_link)
    self.route('/test', method='GET', callback=self.test)
    self.route('/nodes/<node_name>/cmd', method='POST', callback=self.do_cmd)
    self.route('/events/<dpid>', method='GET', callback=self.get_events_page)
    self.route('/', method = 'OPTIONS', callback=self.options_handler)
    self.route('/<path:path>', method = 'OPTIONS', callback=self.options_handler)

  def options_handler(self, path = None):
      return

  def test(self):
    return "TEST!"

  def post_node(self, node_name):
    node = self.net[node_name]
    node.params.update(request.json['params'])

  def add_switch(self, switch_name):
    if switch_name not in self.switch_list:
      c1 = self.net.get('c0')
      str_mac = ':'.join(hex(self.starting_mac)[i:i+2] for i in range(0,12,2))
      s = self.net.addSwitch(switch_name, OVSSwitch, mac=str_mac)
      self.starting_mac += 1 
      s.params.update(request.json['params'])
      s.cmd('ovs-vsctl set Bridge %s protocols=OpenFlow13' % switch_name)
      s.start([c1])
      self.switch_list.append(switch_name)
    else:
      response.status = 403

  def del_switch(self, switch_name):
    if switch_name in self.switch_list:
      self.net.get(switch_name).stop(True)
      self.net.get(switch_name).terminate()
      self.net.get(switch_name).cleanup()
      self.switch_list.remove(switch_name)
    else:
      response.status = 403

  def del_link(self):
    a = request.json['a']
    b = request.json['b']
    if a not in self.switch_list or b not in self.switch_list:
      response.status = 403
    else:
      self.net.configLinkStatus(a, b, 'down')
      self.net.start()

  def add_link(self):
    a = request.json['a']
    b = request.json['b']
    if a not in self.switch_list or b not in self.switch_list:
      response.status = 403
    else:
      self.net.addLink(self.net.get(a), self.net.get(b))
      self.net.configLinkStatus(a, b, 'up')
      self.net.start()

  def do_cmd(self, node_name):
    print(request.query['timeout'])
    timeout = float(request.query['timeout'])
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
      if exec_time > timeout:
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
    
    output = output.replace('<', '&lt;')
    output = output.replace('>', '&gt;')

    output = output.replace('\n', '<br>')
    return output

  def get_events_page(self, dpid):
    perpage = int(request.query['perpage'])
    startat = int(request.query['page'])*perpage

    db_query = 'SELECT from_mac, to_mac, from_port, to_port, ts FROM send_events WHERE dpid = %s ORDER BY ts DESC LIMIT %s OFFSET %s;'
    self.cursor.execute(db_query, (dpid,startat,perpage))

    hdrs = [x[0] for x in self.cursor.description]
    rv = self.cursor.fetchall()
    res=[]
    for el in rv:
      res.append(dict(zip(hdrs, el)))
    return json.dumps(res, indent=4, sort_keys=True, default=str)
  
