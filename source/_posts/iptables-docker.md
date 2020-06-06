---
title: iptables docker
date: 2020-05-25 19:35:05
tags: [linux, docker]
categories: [docker]
keywords: [docker iptables]
description: docker在iptables中增加chain，实现网络隔离和转发（其中一种方式）。
---

# docker增加的chain

docker v18以后有4个iptables chain：
- DOCKER
- DOCKER-USER
- DOCKER-ISOLATION-STAGE-1
- DOCKER-ISOLATION-STAGE-2
<!-- more -->


## DOCKER链和DOCKER-USER链

DOCKER链处理理从宿主机到docker0的IP数据包。
如果有自定义的规则，并且在`DOCKER` chain之前生效，则使用`DOCKER-USER`。
```sh
[root@master-29 ~]# iptables --list DOCKER
Chain DOCKER (1 references)
target     prot opt source               destination

[root@master-29 ~]# iptables --list DOCKER-USER
Chain DOCKER-USER (1 references)
target     prot opt source               destination         
RETURN     all  --  anywhere             anywhere
```

## DOCKER-ISOLATION-STAGE链

2条DOCKER-ISOLATION-STAGE链是为了隔离在不同的bridge网络之间的容器。

摘抄自《[基于iptables的Docker网络隔离与通信详解](https://blog.csdn.net/taiyangdao/article/details/88844558)》
>DOCKER-ISOLATION-STAGE-1链过滤源地址是bridge网络（默认docker0）的IP数据包，匹配的IP数据包再进入DOCKER-ISOLATION-STAGE-2链处理，不匹配就返回到父链FORWARD。
>在DOCKER-ISOLATION-STAGE-2链中，进一步处理目的地址是bridge网络的IP数据包，匹配的IP数据包表示该IP数据包是从一个bridge网络的网桥发出，到另一个bridge网络的网桥，这样的IP数据包来自其他bridge网络，将被直接DROP；不匹配的IP数据包就返回到父链FORWARD继续进行后续处理。

DOCKER-ISOLATION-STAGE-1处理sourc为docker0的流量。
DOCKER-ISOLATION-STAGE-2处理dest为docker0的流量。
```
[root@master-29 ~]# iptables -nvL DOCKER-ISOLATION-STAGE-1
Chain DOCKER-ISOLATION-STAGE-1 (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 DOCKER-ISOLATION-STAGE-2  all  --  docker0 !docker0  0.0.0.0/0            0.0.0.0/0           
1543K  582M RETURN     all  --  *      *       0.0.0.0/0            0.0.0.0/0           


[root@master-29 ~]# iptables -nvL DOCKER-ISOLATION-STAGE-2
Chain DOCKER-ISOLATION-STAGE-2 (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 DROP       all  --  *      docker0  0.0.0.0/0            0.0.0.0/0           
    0     0 RETURN     all  --  *      *       0.0.0.0/0            0.0.0.0/0  
```

也可以用iptables-save观察，nat表规则：
```sh
*nat
:PREROUTING ACCEPT [14084225:999405411]
:INPUT ACCEPT [14083892:999374948]
:OUTPUT ACCEPT [82455:5057925]
:POSTROUTING ACCEPT [82455:5057925]
:DOCKER - [0:0]
# 1 对于发向本地的包，都经过DOCKER链
-A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER
# 2 目标地址不是127.0.0.0/8、且发向本地的包，都经过DOCKER链
-A OUTPUT ! -d 127.0.0.0/8 -m addrtype --dst-type LOCAL -j DOCKER
# 3 源地址为172.17.0.0/16 （docker容器）、并且目标接口不是docker0（即发向外部流量），进行MASQUERADE（源地址转换成主机网卡的地址）。
-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
# 4 来自docker0的流量，返回上一级链处理
-A DOCKER -i docker0 -j RETURN
```

filter表规则：
```sh
*filter
:INPUT ACCEPT [587512631:125743990396]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [423226964:67793677714]
:DOCKER - [0:0]
:DOCKER-ISOLATION-STAGE-1 - [0:0]
:DOCKER-ISOLATION-STAGE-2 - [0:0]
:DOCKER-USER - [0:0]
-A INPUT -i virbr0 -p udp -m udp --dport 53 -j ACCEPT
-A INPUT -i virbr0 -p tcp -m tcp --dport 53 -j ACCEPT
-A INPUT -i virbr0 -p udp -m udp --dport 67 -j ACCEPT
-A INPUT -i virbr0 -p tcp -m tcp --dport 67 -j ACCEPT
-A FORWARD -j DOCKER-USER
-A FORWARD -j DOCKER-ISOLATION-STAGE-1
-A FORWARD -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o docker0 -j DOCKER
-A FORWARD -i docker0 ! -o docker0 -j ACCEPT
-A FORWARD -i docker0 -o docker0 -j ACCEPT
-A FORWARD -o br-8fc7e4e9385e -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -o br-8fc7e4e9385e -j DOCKER
-A FORWARD -i br-8fc7e4e9385e ! -o br-8fc7e4e9385e -j ACCEPT
-A FORWARD -i br-8fc7e4e9385e -o br-8fc7e4e9385e -j ACCEPT
-A FORWARD -d 192.168.122.0/24 -o virbr0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -s 192.168.122.0/24 -i virbr0 -j ACCEPT
-A FORWARD -i virbr0 -o virbr0 -j ACCEPT
-A FORWARD -o virbr0 -j REJECT --reject-with icmp-port-unreachable
-A FORWARD -i virbr0 -j REJECT --reject-with icmp-port-unreachable
-A OUTPUT -o virbr0 -p udp -m udp --dport 68 -j ACCEPT
# 来自docker0、并且不是发向docker0的包，执行DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -i docker0 ! -o docker0 -j DOCKER-ISOLATION-STAGE-2
-A DOCKER-ISOLATION-STAGE-1 -i br-8fc7e4e9385e ! -o br-8fc7e4e9385e -j DOCKER-ISOLATION-STAGE-2
# 返回上一层链处理
-A DOCKER-ISOLATION-STAGE-1 -j RETURN
# stage-2中，发向docker0的包都丢弃
-A DOCKER-ISOLATION-STAGE-2 -o docker0 -j DROP
-A DOCKER-ISOLATION-STAGE-2 -o br-8fc7e4e9385e -j DROP
# 返回上一层链处理
-A DOCKER-ISOLATION-STAGE-2 -j RETURN
-A DOCKER-USER -j RETURN
```


# 限制访问docker host

默认情况下，所有流量都可以访问docker主机。以下是限制只允许`192.168.1.1`访问docker host：
```
iptables -I DOCKER-USER -i ext_if ! -s 192.168.1.1 -j DROP
```

##允许docker主机转发流量

docker默认设置FORWARD链为DROP。
如果docker主机恰好是router，则需要设置：
```
iptables -I DOCKER-USER -i src_if -o dst_if -j ACCEPT
```


# 参考

- [Docker and iptables](https://docs.docker.com/network/iptables/#add-iptables-policies-before-dockers-rules)
- [基于iptables的Docker网络隔离与通信详解](https://blog.csdn.net/taiyangdao/article/details/88844558)
- [理解 Docker 网络(一) -- Docker 对宿主机网络环境的影响](https://zhuanlan.zhihu.com/p/59538531)
- [Use bridge networks](https://docs.docker.com/network/bridge/)
- [docker的几种原生网络模式](https://www.cnblogs.com/wshenjin/p/9720067.html)

