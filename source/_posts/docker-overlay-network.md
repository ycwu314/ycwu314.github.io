---
title: docker overlay network 实验
date: 2020-06-02 20:39:10
tags: [docker, etcd]
categories: [docker]
keywords: [docker etcd overlay]
description: 使用etcd集群搭建docker overlay网络
---

# 部署结构

两台机器143、109，使用2376端口通信。
使用docker compose搭建etcd集群，部署在143。

{% asset_img overlay.png overlay %}
<!-- more -->

# 使用docker compose部署etcd集群

```yml
version: '3'
networks: 
  myetcd: 

volumes:
  data-etcd1:
  data-etcd2:
  data-etcd3:

services:
  etcd1:
    image: quay.io/coreos/etcd
    container_name: etcd1
    command: etcd -name etcd1 -advertise-client-urls http://etcd1:12379 -listen-client-urls http://0.0.0.0:2379 -listen-peer-urls http://0.0.0.0:2380 -initial-cluster-token etcd-cluster -initial-cluster "etcd1=http://etcd1:2380,etcd2=http://etcd2:2380,etcd3=http://etcd3:2380" -initial-cluster-state new
    ports:
      - 12379:2379
      - 12380:2380
    volumes:
      - data-etcd1:/etcd-data
    networks:
      - myetcd
 
  etcd2:
    image: quay.io/coreos/etcd
    container_name: etcd2
    command: etcd -name etcd2 -advertise-client-urls http://etcd2:22379 -listen-client-urls http://0.0.0.0:2379 -listen-peer-urls http://0.0.0.0:2380 -initial-cluster-token etcd-cluster -initial-cluster "etcd1=http://etcd1:2380,etcd2=http://etcd2:2380,etcd3=http://etcd3:2380" -initial-cluster-state new
    ports:
      - 22379:2379
      - 22380:2380
    volumes:
      - data-etcd2:/etcd-data
    networks:
       - myetcd
  
  etcd3:
    image: quay.io/coreos/etcd
    container_name: etcd3
    command: etcd -name etcd3 -advertise-client-urls http://etcd3:32379 -listen-client-urls http://0.0.0.0:2379 -listen-peer-urls http://0.0.0.0:2380 -initial-cluster-token etcd-cluster -initial-cluster "etcd1=http://etcd1:2380,etcd2=http://etcd2:2380,etcd3=http://etcd3:2380" -initial-cluster-state new
    ports:
      - 32379:2379
      - 32380:2380
    volumes:
      - data-etcd3:/etcd-data
    networks:
      - myetcd
```
etcd使用2个端口，一个用于集群通信，一个用于客户端访问。
集群（cluster、peer）使用2380。客户端（client）使用2379。3个实例的对外端口分别增加1w、2w、3w，并且映射到宿主机，方便做实验。


注意几个选项：
- -advertise-client-urls：通知其他ETCD节点，当前客户端接入本节点的监听地址。
- -listen-client-urls： 客户端请求监听地址。`0.0.0.0`为允许接收任意ip的请求。
- -listen-peer-urls： 本节点与其他节点进行数据交换(选举，数据同步)的监听地址。`0.0.0.0`为允许接收任意ip的请求。

docker实例必须能够访问`-advertise-client-urls`，因此上面的yaml把该项设置为**external端口**。（其实也可以使用host网络）

另外，etcd规定，如果`--listen-client-urls`被设置了，那么就必须同时设置`--advertise-client-urls`，所以即使设置和默认相同，也必须显式设置。

etcd集群部署在143，为了让109机器正常识别etcd1、etcd2、etcd3主机名（`-advertise-client-urls`选项），在109机器hosts文件增加映射到143。

启动上面的etcd集群
```
docker-compose up -d 
```

# 修改docker service

## node143

```
[root@host143 etcd]# vi /lib/systemd/system/docker.service
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock -H unix:///var/run/docker.sock  -H tcp://0.0.0.0:2376 --cluster-store=etcd://172.25.20.143:12379 --cluster-advertise=172.25.20.143:2376

[root@host143 etcd]# systemctl daemon-reload
[root@host143 etcd]# service docker restart
Redirecting to /bin/systemctl restart docker.service
```

注意选项：
- `--cluster-store`是分布式存储，支持etcd、consul、zookeeper。
- `--cluster-advertise`是本docker实例对外公告的地址

这里挖了个坑：143机器上使用docker-compose部署了etcd集群，那么docker重启并没有自动拉起docker compose的etcd集群，导致报错。
使用`journalctl -fu docker`看到的日志：
```
Error response from daemon: pool configuration failed because of 100: Key not found (/docker/network/v1.0/ipam) [28]
```

解决：
- 修改docker.service文件，重启docker之后，再建立etcd集群。



## node109

```
[root@host109 etcd]# vi /lib/systemd/system/docker.service
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock -H unix:///var/run/docker.sock  -H tcp://0.0.0.0:2376 --cluster-store=etcd://172.25.20.143:12379 --cluster-advertise=172.25.22.109:2376

[root@host109 etcd]# systemctl daemon-reload
[root@host109 etcd]# service docker restart
Redirecting to /bin/systemctl restart docker.service
```

## 开启forwarding

检查forwarding是否开启
```
sysctl net.ipv4.conf.all.forwarding=1
iptables -P FORWARD ACCEPT
```


# 创建overlay网络

在node143创建overlay网络
```
docker network create --driver overlay myoverlay
```

在node109上可以看到myoverlay，注意scope为global。
```
(base) [root@publicService ~]# docker network ls
NETWORK ID          NAME                     DRIVER              SCOPE
e376d138725b        bridge                   bridge              local
f0adf93c5be7        docker_gwbridge          bridge              local
17ddb8efc8f4        host                     host                local
667bb5b0b972        myoverlay                overlay             global
16ebe9d2b2e0        none                     null                local
```


# 观察容器网络连通性

在143执行
```
# --network 指定使用的网络
docker run --network myoverlay --rm -it --name alpine_143 alpine:3.11.6 sh

/ # ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
301: eth0@if302: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1450 qdisc noqueue state UP 
    link/ether 02:42:0a:00:00:02 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.2/24 brd 10.0.0.255 scope global eth0
       valid_lft forever preferred_lft forever
303: eth1@if304: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue state UP 
    link/ether 02:42:ac:13:00:02 brd ff:ff:ff:ff:ff:ff
    inet 172.19.0.2/16 brd 172.19.255.255 scope global eth1
       valid_lft forever preferred_lft forever
```
143有2个网卡：
- eth0: 指向overlay网络，分配地址10.0.0.2
- eth1: 私有网络，分配地址172.19.0.2

在109执行
```
docker run --network myoverlay --rm -it --name alpine_109 alpine:3.11.6 sh

/ # ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
274: eth0@if275: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1450 qdisc noqueue state UP 
    link/ether 02:42:0a:00:00:03 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.3/24 brd 10.0.0.255 scope global eth0
       valid_lft forever preferred_lft forever
276: eth1@if277: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue state UP 
    link/ether 02:42:ac:12:00:02 brd ff:ff:ff:ff:ff:ff
    inet 172.18.0.2/16 brd 172.18.255.255 scope global eth1
       valid_lft forever preferred_lft forever
```
109有2个网卡：
- eth0: 指向overlay网络，分配地址10.0.0.3
- eth1: 私有网络，分配地址172.18.0.2

同时在143或者109观察overlay网络
```
(base) [root@publicService ~]# docker network inspect  myoverlay

[
    {
        "Name": "myoverlay",
        "Id": "667bb5b0b97288d859292ba35378d3b927c2bfda9ec39e7e0a49d1d6f927d33e",
        "Created": "2020-06-02T17:01:15.959652724+08:00",
        "Scope": "global",
        "Driver": "overlay",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": {},
            "Config": [
                {
                    "Subnet": "10.0.0.0/24",
                    "Gateway": "10.0.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Ingress": false,
        "ConfigFrom": {
            "Network": ""
        },
        "ConfigOnly": false,
        "Containers": {
            "95686ec61aa208df6b51cb5b07296e7971c780746cd3414716d81f14292047a3": {
                "Name": "alpine_109",
                "EndpointID": "40eac211fea5351a39d5c0874c106c752f9aea3db76cb393772d8023d0ef7e4c",
                "MacAddress": "02:42:0a:00:00:03",
                "IPv4Address": "10.0.0.3/24",
                "IPv6Address": ""
            },
            "ep-646ed81e8f2c0a527389e0b44ec9087436634d1a9f0710900efaa5ffd3bf94f7": {
                "Name": "alpine_143",
                "EndpointID": "646ed81e8f2c0a527389e0b44ec9087436634d1a9f0710900efaa5ffd3bf94f7",
                "MacAddress": "02:42:0a:00:00:02",
                "IPv4Address": "10.0.0.2/24",
                "IPv6Address": ""
            }
        },
        "Options": {},
        "Labels": {}
    }
]
```
overlay网络分配了子网`10.0.0.0/24`。


测试网络联通性，在alpine_143 ping alpine_109:
```
/ # ping 10.0.0.3
PING 10.0.0.3 (10.0.0.3): 56 data bytes
64 bytes from 10.0.0.3: seq=0 ttl=64 time=0.440 ms
64 bytes from 10.0.0.3: seq=1 ttl=64 time=0.338 ms
64 bytes from 10.0.0.3: seq=2 ttl=64 time=0.234 ms
^C
--- 10.0.0.3 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.234/0.337/0.440 ms
```

重温题图：
{% asset_img overlay.png overlay %}

