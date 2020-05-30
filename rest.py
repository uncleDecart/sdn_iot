#!/usr/bin/python
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

from interactive_topo import TopoHandler, MyTopo

CONTROLLER_HOST = '0.0.0.0'
CONTROLLER_PORT = '5555'
CONTROLLER_URI = 'http://{}:{}/'.format(CONTROLLER_HOST, CONTROLLER_PORT)

setLogLevel('debug')

class Dispatcher(Bottle):
  def __init__(self):
    super(Dispatcher, self).__init__()
    config = {
      'user' : 'root',
      'password' : 'root',
      'host' : 'db',
      'port' : '3306',
      'database' : 'emulator'
    }
    self.connection = mysql.connector.connect(**config)
    self.connection.autocommit = True
    self.cursor = self.connection.cursor()

    self.topo_handler = TopoHandler()
    self.ryu_cmd = "ryu-manager --observe-links --wsapi-host %s --wsapi-port %s ryu.app.iot_switch&" % (CONTROLLER_HOST, CONTROLLER_PORT)

    self.is_net_started = False 
    self.start_net()

    self.starting_mac = 0x1E0BFA737000 # 1E:0B:FA:73:70:00

    self.route('/nodes/<node_name>', method='POST', callback=self.post_node)
    self.route('/switch/<switch_name>', method='POST', callback=self.add_switch)
    self.route('/switch/<switch_name>', method='DELETE', callback=self.del_switch)
    self.route('/host/<host_name>', method='POST', callback=self.add_host)
    self.route('/host/<host_name>', method='DELETE', callback=self.del_host)
    self.route('/link', method='POST', callback=self.add_link)
    self.route('/link', method='DELETE', callback=self.del_link)
    self.route('/test', method='GET', callback=self.test)
    self.route('/nodes/<node_name>/cmd', method='POST', callback=self.do_cmd)

    self.route('/events/<dpid>', method='GET', callback=self.get_events_page)
    self.route('/events/<dpid>/total', method='GET', callback=self.get_events_total)
    self.route('/events/charge_state', method='GET', callback=self.get_charge_state)
    self.route('/count/events', method='GET', callback=self.get_events_count)
    self.route('/events/<dpid>/charge_events', method='GET', callback=self.get_charge_events)
    self.route('/events/<dpid>/charge_events/total', method='GET', callback=self.get_charge_total)

    self.route('/', method = 'OPTIONS', callback=self.options_handler)
    self.route('/<path:path>', method = 'OPTIONS', callback=self.options_handler)

    self.route('/net/start', method='GET', callback=self.start_net)
    self.route('/net/stop', method='GET', callback=self.stop_net)
    self.route('/net/status', method='GET', callback=self.net_status)
    self.route('/net/topo', method='GET', callback=self.get_topology)

  def options_handler(self, path = None):
      return

  def start_net(self):
    if self.is_net_started:
      response.status = 403
    else:

      self.cursor.execute('DELETE FROM topology')
      for node_a, node_b in self.topo_handler.get_links():
        self.cursor.execute("REPLACE INTO topology (node_a, node_b) VALUES (%s, %s)",
                            (node_a, node_b))
      self.connection.commit()

      self.net = Mininet(MyTopo(self.topo_handler), switch=OVSSwitch,
                         controller=RemoteController('c0', ip='127.0.0.1', port=6653))
      self.net.start()
      self.net['c0'].cmd(self.ryu_cmd)
      self.update_mac_to_dpid()
      self.net.pingAll()
      ts = time.time()
      timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
      while True:
        try:
          l = requests.get('http://localhost:5555/v1.0/topology/switches').json()
          break
        except:
          time.sleep(10)

      for el in l:
        self.cursor.execute("REPLACE INTO charge_state (dpid, charge, ts) VALUES (%s, %s, %s)",
                            (el['dpid'], 10000, timestamp))
      self.connection.commit()
      self.is_net_started = True
 
  def stop_net(self):
    if not self.is_net_started:
      response.status = 403
    else:
      self.net.stop()
      os.system('fuser -k 6653/tcp') # kill mininet controller
      self.is_net_started = False 

  def net_status(self):
    return {"status" : self.is_net_started}

  def update_mac_to_dpid(self):
    self.cursor.execute("DELETE FROM mac_to_dpid")
    l = requests.get('http://localhost:5555/v1.0/topology/switches').json()
    for el in l:
      for mac in el['ports']:
        self.cursor.execute("REPLACE INTO mac_to_dpid (mac_addr, dpid) VALUES (%s, %s)",
                            (mac['hw_addr'], el['dpid']))
    l = requests.get('http://localhost:5555/v1.0/topology/hosts').json()

    for el in l:
      self.cursor.execute("REPLACE INTO mac_to_dpid (mac_addr, dpid) VALUES (%s, %s)",
                          (el['port']['hw_addr'],
                          'h'+el['ipv4'][0].split('.')[-1]))
    self.connection.commit()

  def test(self):
    return "TEST!"

  def post_node(self, node_name):
    if not self.is_net_started:
      response.status = 403
    else:
      node = self.net[node_name]
      node.params.update(request.json['params'])

  def add_switch(self, switch_name):
    if switch_name not in self.topo_handler.get_switches() and not self.is_net_started:
      c0 = self.net.get('c0')
      str_mac = ':'.join(hex(self.starting_mac)[i:i+2] for i in range(0,12,2))
      self.topo_handler.add_switch(switch_name)
      self.starting_mac += 1 
    else:
      response.status = 403

  def add_host(self, host_name):
    if host_name not in self.topo_handler.get_switches() and not self.is_net_started:
      self.topo_handler.add_host(host_name)
    else:
      response.status = 403

  def del_switch(self, switch_name):
    if switch_name in self.topo_handler.get_switches() and not self.is_net_started:
      self.topo_handler.delete_switch(switch_name)
    else:
      response.status = 403

  def del_host(self, host_name):
    if host_name in self.topo_handler.get_hosts() and not self.is_net_started:
      self.topo_handler.delete_host(host_name)
    else:
      response.status = 403

  def del_link(self):
    a = request.json['a']
    b = request.json['b']
    has_link = ((a,b) not in self.topo_handler.get_links() and (b,a) not in self.topo_handler.get_links())
    if has_link or self.is_net_started:
      response.status = 403
    else:
      self.net.configLinkStatus(a, b, 'down')
      if (a,b) in self.topo_handler.get_links():
        self.topo_handler.delete_link((a,b))
      else:
        self.topo_handler.delete_link((b,a))
      self.net.start()

  def is_node(self, name):
    return name in self.topo_handler.get_switches() or name in self.topo_handler.get_hosts() 

  def add_link(self):
    a = request.json['a']
    b = request.json['b']
    nodes = self.is_node(a) and self.is_node(b)
    if not nodes or self.is_net_started:
      response.status = 403
    else:
      self.topo_handler.add_link((a,b))

  def get_topology(self):
    return {"hosts" : list(self.topo_handler.get_hosts()),
            "switches" : list(self.topo_handler.get_switches()),
            "links" : self.topo_handler.get_links()}


  def do_cmd(self, node_name):
    if not self.is_net_started:
      response.status = 403
    else:
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

  def get_events_count(self):
    start = request.query['start']
    end = request.query['end']

    db_query = 'select dpid, count(*) as events from charge_events where ts >= %s and ts <= %s group by dpid'
    return self.jsonify_query(db_query, start, end)

  def get_events_total(self, dpid):
    db_query = 'SELECT count(*) as total FROM send_events WHERE dpid = %s'
    return self.jsonify_query(db_query, dpid)

  def get_events_page(self, dpid):
    perpage = int(request.query['perpage'])
    startat = int(request.query['page'])*perpage

    db_query = self.paginate('SELECT from_mac, to_mac, from_port, to_port, ts FROM send_events WHERE dpid = %s')
    return self.jsonify_query(db_query, dpid, perpage, startat)

  def get_charge_state(self):
    if not self.is_net_started:
      response.status = 403
    else:
      return self.jsonify_query('SELECT * FROM charge_state')

  def get_charge_total(self, dpid):
    db_query = 'SELECT count(*) as total FROM charge_events WHERE dpid = %s'
    return self.jsonify_query(db_query, dpid)

  def get_charge_events(self, dpid):
    perpage = int(request.query['perpage'])
    startat = int(request.query['page'])*perpage
    return self.jsonify_query(self.paginate('SELECT * FROM charge_events WHERE dpid = %s'), dpid, perpage, startat)

  def paginate(self, query):
    return query + ' ORDER BY id DESC LIMIT %s OFFSET %s;'


  def jsonify_query(self, db_query, *args):
    self.cursor.execute(db_query, args)

    hdrs = [x[0] for x in self.cursor.description]
    rv = self.cursor.fetchall()
    res=[]
    for el in rv:
      res.append(dict(zip(hdrs, el)))
    response.content_type = 'application/json'
    return json.dumps(res, indent=4, sort_keys=True, default=str)

