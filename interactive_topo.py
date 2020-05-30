from mininet.topo import Topo

class TopoHandler(): 
  def __init__(self):
    self.hosts_starting_mac = 0
    self.my_hosts = {'h1', 'h2', 'h3'}
    self.my_switches = {'s1', 's2', 's3'}
    self.my_links = [('s1', 'h1'), ('s2', 'h2'), ('s3', 'h3'), ('s1', 's2'), ('s2', 's3'), ('s3', 's1')]

  def add_host(self, name):
    self.my_hosts.add(name) 
  def add_switch(self, name):
    self.my_switches.add(name) 
  def add_link(self, l):
    self.my_links.append(l)

  def delete_host(self, name):
    self.my_hosts.remove(name)
    self.delete_related_links(name)
  def delete_switch(self, name):
    self.my_switches.remove(name)
    self.delete_related_links(name)
  def delete_link(self, l):
    self.my_links.remove(l)
  def delete_related_links(self, name):
    self.my_links = [i for i in self.my_links if i[1] != name and i[0] != name] 

  def get_hosts(self):
    return self.my_hosts
  def get_switches(self):
    return self.my_switches
  def get_links(self):
    return self.my_links

  def get_host_mac(self, name):
    idx = int(name[1:])
    mac_hex = "{:012x}".format(self.hosts_starting_mac+idx)
    mac_str = ":".join(mac_hex[i:i+2] for i in range(0, len(mac_hex), 2))
    return mac_str

class MyTopo( Topo ):
  def __init__(self, topo_handler, *args, **kwargs):
    self.topo_handler = topo_handler
    super(self.__class__, self).__init__(*args, **kwargs)

  def build( self ):
    impl = {};
    for host in self.topo_handler.get_hosts():
      impl[host] = self.addHost(host, mac=self.topo_handler.get_host_mac(host))

    for switch in self.topo_handler.get_switches():
      impl[switch] = self.addSwitch(switch)

    for a, b in self.topo_handler.get_links():
      self.addLink(impl[a], impl[b])

