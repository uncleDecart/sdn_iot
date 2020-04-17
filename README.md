Openflow SDN aplication controller based on ryu 

Run:

```
docker build -t dispatcher . 
docker run -it -p 5555-5556:5555-5556 --rm --privileged -e DISPLAY \
           -v /tmp/.X11-unix:/tmp/.X11-unix \
           -v /lib/modules:/lib/modules \
           dispatcher:latest
```

Usefull links:
- [Very usefull StackOverflow answer](https://stackoverflow.com/questions/37998065/understanding-ryu-openflow-controller-mininet-wireshark-and-tcpdump)
- [What is SDN](http://flowgrammable.org/sdn/openflow/)
- [SDN in more depth](http://yuba.stanford.edu/~nickm/talks/infocom_brazil_2009_v1-1.pdf)
- [sdnhub ryu tutorial](http://sdnhub.org/tutorials/ryu/)
