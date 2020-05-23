#!/usr/bin/python
from mininet.node import OVSSwitch
from bottle import Bottle, request, response
import time
import json
import mysql.connector
import requests
import datetime

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

    self.net = net
    self.starting_mac = 0x1E0BFA737000 # 1E:0B:FA:73:70:00
    l = requests.get('http://localhost:5555/v1.0/topology/switches').json()
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    for el in l:
      print "FUKKKKKK ME ", el['dpid']
      self.cursor.execute("REPLACE INTO charge_state (dpid, charge, ts) VALUES (%s, %s, %s)", (el['dpid'], 10000, timestamp))
    self.connection.commit()

    self.switch_list = sl[:]
    self.route('/nodes/<node_name>', method='POST', callback=self.post_node)
    self.route('/switch/<switch_name>', method='POST', callback=self.add_switch)
    self.route('/switch/<switch_name>', method='DELETE', callback=self.del_switch)
    self.route('/link', method='POST', callback=self.add_link)
    self.route('/link', method='DELETE', callback=self.del_link)
    self.route('/test', method='GET', callback=self.test)
    self.route('/nodes/<node_name>/cmd', method='POST', callback=self.do_cmd)

    self.route('/events/<dpid>', method='GET', callback=self.get_events_page)
    self.route('/events/<dpid>/total', method='GET', callback=self.get_events_total)
    self.route('/events/<dpid>/charge_state', method='GET', callback=self.get_charge_state)
    self.route('/events/<dpid>/charge_events', method='GET', callback=self.get_charge_events)
    self.route('/events/<dpid>/charge_events/total', method='GET', callback=self.get_charge_total)

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
      c0 = self.net.get('c0')
      str_mac = ':'.join(hex(self.starting_mac)[i:i+2] for i in range(0,12,2))
      s = self.net.addSwitch(switch_name, OVSSwitch, mac=str_mac)
      self.starting_mac += 1 
      s.params.update(request.json['params'])
      s.start([c0])
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

  def get_events_total(self, dpid):
    db_query = 'SELECT count(*) as total FROM send_events WHERE dpid = %s'
    return self.jsonify_query(db_query, dpid)

  def get_events_page(self, dpid):
    perpage = int(request.query['perpage'])
    startat = int(request.query['page'])*perpage

    db_query = self.paginate('SELECT from_mac, to_mac, from_port, to_port, ts FROM send_events WHERE dpid = %s')
    return self.jsonify_query(db_query, dpid, perpage, startat)

  def get_charge_state(self, dpid):
    perpage = int(request.query['perpage'])
    startat = int(request.query['page'])*perpage
    return self.jsonify_query(self.paginate('SELECT * FROM charge_state WHERE dpid = %s'),
                                            dpid, perpage, startat)

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

