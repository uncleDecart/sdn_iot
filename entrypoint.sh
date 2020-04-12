#!/usr/bin/env bash

service openvswitch-switch start
ovs-vsctl set-manager ptcp:6640
#ryu-manager --observe-links iot_switch.py &
python network_handler.py
# --ofp-tcp-listen-port 6634
service openvswitch-switch stop
