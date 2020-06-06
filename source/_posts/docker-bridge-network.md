---
title: docker bridge network 实验
date: 2020-06-02 21:13:53
tags: [docker]
categories: [docker]
keywords: [docker bridge]
description: docker bridge网络实验。
---

创建自定义brdige，并且观察。
<!-- more -->
```sh
[root@host143 ~]# docker network create --driver bridge my-net

# 分配了子网网段和网关地址
# 新建容器的时候，可以使用 --ip 指定静态ip，重启容器不会改变ip
[root@host143 ~]# docker network inspect my-net
[
    {
        "Name": "my-net",
        # Id也是bridge id
        "Id": "c8a0eda8ec92485fbb60035ef38fd8a36b71adf0f0f7cc23832f1fe7a70168d8",
        "Created": "2020-05-26T19:57:15.748691755+08:00",
        "Scope": "local",
        "Driver": "bridge",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": {},
            "Config": [
                {
                    "Subnet": "172.18.0.0/16",
                    "Gateway": "172.18.0.1"
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
        "Containers": {},
        "Options": {},
        "Labels": {}
    }
]

# 新建的bridge name就是br-[bridge id]
[root@host143 ~]# brctl show
bridge name	bridge id		STP enabled	interfaces
br-8fc7e4e9385e		8000.024215e9e52d	no		
# c8a0eda8ec92 对应 bridge id
br-c8a0eda8ec92		8000.0242b1af64a8	no		
docker0		8000.0242a0f4db57	no		
virbr0		8000.525400471166	yes		virbr0-nic
```

使用自定义bridge：
```sh
[root@host143 ~]# docker create --rm --name my-alpine --network my-net alpine:latest top
WARNING: IPv4 forwarding is disabled. Networking will not work.
25c20e848724ce6623dbe05b488e5e738631852e66d990ecd934a19b9644d907

[root@host143 ~]# docker start my-alpine

[root@host143 ~]# docker exec -it my-alpine ping baidu.com
ping: bad address 'baidu.com'
```
为什么ping不同外部网络呢？
>By default, traffic from containers connected to the default bridge network is not forwarded to the outside world. 

为了解决从docker容器到bridge网络不会转发到外部，要开启forwarding：
```sh
# 查看
[root@host143 ~]# sysctl net.ipv4.conf.all.forwarding
net.ipv4.conf.all.forwarding = 0

# 修改forwarding
[root@host143 ~]# sysctl net.ipv4.conf.all.forwarding=1
net.ipv4.conf.all.forwarding = 1

# 修改forward链
[root@host143 ~]# iptables -P FORWARD ACCEPT

[root@host143 ~]# docker exec -it my-alpine ping baidu.com
PING baidu.com (220.181.38.148): 56 data bytes
64 bytes from 220.181.38.148: seq=0 ttl=49 time=37.772 ms
```

docker不同network的隔离，表现在2条isolation-stage链：
```sh
*filter
# br-c8a0eda8ec92是刚才建立my-net的网卡。
# 来源于br-c8a0eda8ec92、并且发送到docker0的包，都丢弃
# 来源于docker0、并且发送到br-c8a0eda8ec92的包，都丢弃
-A DOCKER-ISOLATION-STAGE-1 -i br-c8a0eda8ec92 ! -o br-c8a0eda8ec92 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -i docker0 ! -o docker0 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -j RETURN
-A DOCKER-ISOLATION-STAGE-2 -o br-c8a0eda8ec92 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -o docker0 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -j RETURN
```

如果要连同2个网络，使用connect命令：

```sh
[root@host143 ~]# docker network create --driver bridge my-net2
2e46e8012ef53d54f59467544f432989797989c1792dfc772812d71e114d3eb8

[root@host143 ~]# docker network inspect my-net2
[
    {
        "Name": "my-net2",
        "Id": "2e46e8012ef53d54f59467544f432989797989c1792dfc772812d71e114d3eb8",
        "Created": "2020-05-27T14:21:59.300644879+08:00",
        "Scope": "local",
        "Driver": "bridge",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": {},
            "Config": [
                {
                    "Subnet": "172.20.0.0/16",
                    "Gateway": "172.20.0.1"
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
        "Containers": {},
        "Options": {},
        "Labels": {}
    }
]

[root@host143 ~]# brctl show
bridge name	bridge id		STP enabled	interfaces
br-2e46e8012ef5		8000.0242c0a774bf	no		
br-8fc7e4e9385e		8000.024215e9e52d	no		
br-c8a0eda8ec92		8000.0242b1af64a8	no		
docker0		8000.0242a0f4db57	no		
virbr0		8000.525400471166	yes		virbr0-nic

```

```sh
[root@host143 ~]# docker create --rm --name my-alpine --network my-net alpine:latest top
428ff5effcb821205a7a899235d399831e24db47b239919d12ed3feb5b1a6711

[root@host143 ~]# docker network connect my-net2 my-alpine

[root@host143 ~]# docker inspect --format='{{json .NetworkSettings.Networks}}'  my-alpine 
# 省略其他输出
            "Networks": {
                "my-net": {
                    "IPAMConfig": null,
                    "Links": null,
                    "Aliases": null,
                    "NetworkID": "",
                    "EndpointID": "",
                    "Gateway": "",
                    "IPAddress": "",
                    "IPPrefixLen": 0,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "",
                    "DriverOpts": null
                },
                "my-net2": {
                    "IPAMConfig": {},
                    "Links": null,
                    "Aliases": [
                        "428ff5effcb8"
                    ],
                    "NetworkID": "",
                    "EndpointID": "",
                    "Gateway": "",
                    "IPAddress": "",
                    "IPPrefixLen": 0,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "",
                    "DriverOpts": {}
                }
            }
```

iptables-save查看规则变化。
br-c8a0eda8ec92对应my-net。br-2e46e8012ef5对应my-net2。
```
*filter
-A DOCKER-ISOLATION-STAGE-1 -i br-2e46e8012ef5 ! -o br-2e46e8012ef5 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -i br-c8a0eda8ec92 ! -o br-c8a0eda8ec92 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -i docker0 ! -o docker0 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -j RETURN
-A DOCKER-ISOLATION-STAGE-2 -o br-2e46e8012ef5 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -o docker0 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -j RETURN
```

更直观的是ifconfig，注意两张网卡的网段。
```sh
[root@host143 ~]# docker exec -it my-alpine sh
/ # ifconfig
# 对应my-net
eth0      Link encap:Ethernet  HWaddr 02:42:AC:12:00:02  
          inet addr:172.18.0.2  Bcast:172.18.255.255  Mask:255.255.0.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:8 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0 
          RX bytes:648 (648.0 B)  TX bytes:0 (0.0 B)

# 对应my-net2
eth1      Link encap:Ethernet  HWaddr 02:42:AC:14:00:02  
          inet addr:172.20.0.2  Bcast:172.20.255.255  Mask:255.255.0.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:24 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0 
          RX bytes:2634 (2.5 KiB)  TX bytes:0 (0.0 B)
```

使用`docker network disconnect`可以实时取消自定义网络，且不需要重启容器。
