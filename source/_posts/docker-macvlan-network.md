---
title: docker-macvlan-network
date: 2020-06-03 11:39:23
tags:
categories:
keywords:
description:
---
{% asset_img slug [title] %}


# 混杂模式

默认情况下网卡只把发给本机的包（包括广播包）传递给上层程序，其它的包一律丢弃。
混杂模式（Promiscuous Mode）是指一台机器能够接收所有经过它的数据流，而不论其目的地址是否是它。具体的地址转发则是在接受到数据后由MAC层来进行。
<!-- more -->

使用ifconfig操作promisc模式：
```sh
(base) [root@publicService ~]# ifconfig ens192 
ens192: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.25.22.109  netmask 255.255.252.0  broadcast 172.25.23.255
        inet6 fe80::bca3:c77b:a9b:a75a  prefixlen 64  scopeid 0x20<link>
        ether 00:50:56:b0:80:c6  txqueuelen 1000  (Ethernet)
        RX packets 249274336  bytes 18440080984 (17.1 GiB)
        RX errors 0  dropped 101622  overruns 0  frame 0
        TX packets 17261240  bytes 2476002584 (2.3 GiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

# 开启promisc
(base) [root@publicService ~]# ifconfig ens192 promisc
(base) [root@publicService ~]# ifconfig ens192
ens192: flags=4419<UP,BROADCAST,RUNNING,PROMISC,MULTICAST>  mtu 1500
        inet 172.25.22.109  netmask 255.255.252.0  broadcast 172.25.23.255
        inet6 fe80::bca3:c77b:a9b:a75a  prefixlen 64  scopeid 0x20<link>
        ether 00:50:56:b0:80:c6  txqueuelen 1000  (Ethernet)
        RX packets 249275279  bytes 18440147356 (17.1 GiB)
        RX errors 0  dropped 101622  overruns 0  frame 0
        TX packets 17261309  bytes 2476012173 (2.3 GiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

# 关闭promisc
(base) [root@publicService ~]# ifconfig ens192 -promisc
(base) [root@publicService ~]# ifconfig ens192
ens192: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.25.22.109  netmask 255.255.252.0  broadcast 172.25.23.255
        inet6 fe80::bca3:c77b:a9b:a75a  prefixlen 64  scopeid 0x20<link>
        ether 00:50:56:b0:80:c6  txqueuelen 1000  (Ethernet)
        RX packets 249275622  bytes 18440170311 (17.1 GiB)
        RX errors 0  dropped 101622  overruns 0  frame 0
        TX packets 17261333  bytes 2476015397 (2.3 GiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

或者使用ip命令
```sh
# 开启promisc
(base) [root@publicService ~]# ip link set ens192 promisc on
(base) [root@publicService ~]# ifconfig ens192
ens192: flags=4419<UP,BROADCAST,RUNNING,PROMISC,MULTICAST>  mtu 1500
        inet 172.25.22.109  netmask 255.255.252.0  broadcast 172.25.23.255
        inet6 fe80::bca3:c77b:a9b:a75a  prefixlen 64  scopeid 0x20<link>
        ether 00:50:56:b0:80:c6  txqueuelen 1000  (Ethernet)
        RX packets 249285891  bytes 18440882352 (17.1 GiB)
        RX errors 0  dropped 101622  overruns 0  frame 0
        TX packets 17261762  bytes 2476085900 (2.3 GiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

# 关闭promisc
(base) [root@publicService ~]# ip link set ens192 promisc off
(base) [root@publicService ~]# ifconfig ens192
ens192: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.25.22.109  netmask 255.255.252.0  broadcast 172.25.23.255
        inet6 fe80::bca3:c77b:a9b:a75a  prefixlen 64  scopeid 0x20<link>
        ether 00:50:56:b0:80:c6  txqueuelen 1000  (Ethernet)
        RX packets 249286554  bytes 18440926574 (17.1 GiB)
        RX errors 0  dropped 101622  overruns 0  frame 0
        TX packets 17261792  bytes 2476091316 (2.3 GiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```


# macvlan

macvlan是一种网卡虚拟化技术。允许在同一个物理网卡上配置多个 MAC 地址，即多个 interface，每个 interface 可以配置自己的 IP。
macvlan 的最大优点是性能极好，相比其他实现，macvlan 不需要创建 Linux bridge。
Macvlan 的缺点是需要将主机网卡（NIC）设置为混杂模式（Promiscuous Mode），这在大部分公有云平台上是不允许的。

工作在混乱模式下的物理网卡，其MAC地址会失效，所以，此模式中运行的容器并不能与外网进行通信。

macvlan有四种模式：VEPA，bridge，Private和Passthru

macvlan接口会监听并接收链路上到达本mac地址的报文，因此macvlan（除bridge外）仅能向外部网络发送报文，并接受目的为本机mac的报文。

Mavlan不使用传统的Linux bridge做隔离和区分，而是直接与Linux的以太网接口或者子接口关联，以实现在物理网络中网络和连接的隔离。

Macvlan本身不创建网络，本质上首先使宿主机物理网卡工作在“混杂模式”。

一个网卡只能创建一个 macvlan 网络, 如果要支持多个macvlan网络, 必须使用 sub-interface。



# docker创建macvlan

查找物理网卡对应网关地址
```
(base) [root@publicService opt]# route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         172.25.23.254   0.0.0.0         UG    100    0        0 ens192
172.17.0.0      0.0.0.0         255.255.0.0     U     0      0        0 docker0
172.21.0.0      0.0.0.0         255.255.0.0     U     0      0        0 br-b0a8e75c0663
172.25.20.0     0.0.0.0         255.255.252.0   U     100    0        0 ens192
```


```
docker network create -d macvlan \
--subnet=10.0.100.0/24 \
--ip-range=10.0.100.0/24 \
--gateway=10.0.100.33  \
-o macvlan_mode=bridge \
-o parent=ens192 macvlan
```


```
docker run -it --rm --net=macvlan --ip=10.0.100.100 --name node_1 alpine:3.11.6 sh 
```

docker run -it --rm --net=macvlan --ip=10.0.100.101 --name node_2 alpine:3.11.6 sh 



添加vlan
ip link add link ens192 name ens192.10 type vlan id 10

ip link set dev ens192.10 up

docker network create -d macvlan --subnet=172.16.10.0/24 --gateway=172.16.10.1 -o parent=ens192.10 mac_net10


ip link add link ens192 name ens192.20 type vlan id 20
ip link set dev ens192.20 up


- 在no1上操作docker



docker run -it --rm  --name b1 --ip=172.16.10.10 --network mac_net10 busybox
docker run -itd --name b2 --ip=172.16.20.10 --network mac_net20 busybox


- 在no2上操作docker
docker network create -d macvlan --subnet=172.16.10.0/24 --gateway=172.16.10.1 -o parent=eth0.10 mac_net10
docker network create -d macvlan --subnet=172.16.20.0/24 --gateway=172.16.20.1 -o parent=eth0.20 mac_net20

docker run -itd --name b3 --ip=172.16.10.11 --network mac_net10 busybox
docker run -itd --name b4 --ip=172.16.20.11 --network mac_net20 busybox



# 参考


- [macvlan 一种虚拟网卡解决方案](https://www.jianshu.com/p/2b8b6c738bf6)
- [Docker Macvlan网络驱动使用详解](http://c.biancheng.net/view/3191.html)
- [macvlan和pipework](https://yq.aliyun.com/articles/645839)
- [docker网络之macvlan](https://www.cnblogs.com/charlieroro/p/9656769.html)
- [Docker 网络 host、bridge、macvlan 基本原理和验证](http://yangjunsss.github.io/2018-07-29/Docker-%E7%BD%91%E7%BB%9C-Host-Bridge-Macvlan-%E5%9F%BA%E6%9C%AC%E5%8E%9F%E7%90%86%E5%92%8C%E9%AA%8C%E8%AF%81/)

https://www.cnblogs.com/iiiiher/p/8067226.html

