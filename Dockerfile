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
    ln /usr/bin/ovs-testcontroller /usr/bin/ovs-controller

RUN curl -kL https://github.com/osrg/ryu/archive/master.tar.gz | tar -xvz && \
    mv ryu-master ryu

COPY iot_switch.py ./ryu/ryu/app/
#COPY iot_switch.py ./

RUN pip install -U pip && \
    cd ryu && pip install -r tools/pip-requires && \
    python ./setup.py install

COPY html/ /usr/local/lib/python2.7/dist-packages/ryu/app/gui_topology/html/ 

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY entrypoint.sh network_handler.py rest.py ./
RUN chmod +x entrypoint.sh

EXPOSE 6633 6653 6640 5555 5556

ENTRYPOINT ["./entrypoint.sh"]

