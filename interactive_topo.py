from mininet.topo import Topo

class TopoHandler(): 
  def __init__(self):
    self.my_hosts = {'h1', 'h2'}
    self.my_switches = {'s1', 's2', 's3', 's4'}
    self.my_links = [('h1', 's1'), ('s1', 's2'), ('s2', 's3'), ('s3', 's4'), ('h2', 's4')]

  def add_host(self, name):
    self.my_hosts.add(name) 
  def add_switch(self, name):
    self.my_switches.add(name) 
  def add_link(self, l):
    self.my_links.append(l)

  def delete_host(self, name):
    self.my_hosts.remove(name)
  def delete_switch(self, name):
    self.my_switches.remove(name)
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


class MyTopo( Topo ):
  def __init__(self, topo_handler, *args, **kwargs):
    self.my_hosts = topo_handler.get_hosts()
    self.my_switches = topo_handler.get_switches()
    self.my_links = topo_handler.get_links()
    super(self.__class__, self).__init__(*args, **kwargs)

  def build( self ):
    print("AAAAA ", self.my_links)
    impl = {};
    for host in self.my_hosts:
      impl[host] = self.addHost(host)

    for switch in self.my_switches:
      impl[switch] = self.addSwitch(switch)

    for a, b in self.my_links:
      self.addLink(impl[a], impl[b])

