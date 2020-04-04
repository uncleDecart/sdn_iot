FROM ubuntu:16.04

MAINTAINER Pavel Abramov <uncle.decart@gmail.com>

ENV HOME /root
WORKDIR /root

RUN apt-get update && \
    apt-get install -qy --no-install-recommends python-setuptools python-pip \
        python-eventlet python-lxml python-msgpack curl && \
    rm -rf /var/lib/apt/lists/* && \
    curl -kL https://github.com/osrg/ryu/archive/master.tar.gz | tar -xvz && \
    mv ryu-master ryu && \
    pip install -U pip && \
    cd ryu && pip install -r tools/pip-requires && \
    python ./setup.py install

COPY dispatcher.py requirements.txt ./

RUN pip install -r requirements.txt 

CMD ["ryu-manager", "--observe-links", "dispatcher.py"]
#CMD ["ryu-manager", "--use-syslog", "--observe-links", "dispatcher.py"]
