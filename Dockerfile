FROM debian:9.8-slim

MAINTAINER Pavel Abramov <uncle.decart@gmail.com>

USER root
ENV HOME /root
WORKDIR /root

RUN apt-get update && \
    apt-get install -qy --no-install-recommends \
    python-setuptools \
    python-pip \
    python-eventlet \
    python-lxml \
    python-msgpack \
    curl \
    iproute2 \
    iputils-ping \
    mininet \
    net-tools \
    openvswitch-switch \
    tcpdump \
    openvswitch-testcontroller && \
    rm -rf /var/lib/apt/lists/* && \
    ln /usr/bin/ovs-testcontroller /usr/bin/ovs-controller && \
    curl -kL https://github.com/osrg/ryu/archive/master.tar.gz | tar -xvz && \
    mv ryu-master ryu && \
    pip install -U pip && \
    cd ryu && pip install -r tools/pip-requires && \
    python ./setup.py install

COPY entrypoint.sh dispatcher.py requirements.txt ./

RUN chmod +x entrypoint.sh && \
    pip install -r requirements.txt 

EXPOSE 6633 6653 6640

ENTRYPOINT ["./entrypoint.sh"]

