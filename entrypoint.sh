#!/usr/bin/env bash

service openvswitch-switch start
#ovs-vsctl set-manager ptcp:6640
ryu-manager --verbose --observe-links --ofp-tcp-listen-port 6634 dispatcher.py
# --ofp-tcp-listen-port 6634
service openvswitch-switch stop
