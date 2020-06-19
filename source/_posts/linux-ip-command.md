---
title: linux ip命令
date: 2020-06-18 10:14:32
tags: [linux, network]
categories: [linux]
keywords: [linux ip]
description: ip命令全家桶
---

linux的ip命令能够设置设备、ip地址、路由，功能非常强大。
<!-- more -->

# ip 命令

>ip [ OPTIONS ] OBJECT { COMMAND | help }
>
>OBJECT := { link | addr | addrlabel | route | rule | neigh | tunnel | maddr | mroute | monitor }
>
>OPTIONS := { -V[ersion] | -s[tatistics] | -r[esolve] | -f[amily] { inet | inet6 | ipx | dnet | link } | -o[neline] }

常见的OBJECT有：
- link ：设置设备 (device)，包括 MTU, MAC 地址等等
- addr/address ：设置IP
- route ：路由相关

# ip link

```sh
ip link set { DEVICE | group GROUP }
        [ { up | down } ]                # 停止/启动设备
        [ type ETYPE TYPE_ARGS ]
        [ arp { on | off } ]
        [ dynamic { on | off } ]         # 动态IP
        [ multicast { on | off } ]
        [ allmulticast { on | off } ]
        [ promisc { on | off } ]         # 混杂模式，和macvlan有关
        [ trailers { on | off } ]
        [ txqueuelen PACKETS ]
        [ name NEWNAME ]
        [ address LLADDR ]
        [ broadcast LLADDR ]
        [ mtu MTU ]
        [ netns { PID | NETNSNAME } ]
        [ link-netnsid ID ]
        [ alias NAME ]
        [ vf NUM [ mac LLADDR ]
                 [ vlan VLANID [ qos VLAN-QOS ] ]
                 [ rate TXRATE ]
                 [ max_tx_rate TXRATE ]
                 [ min_tx_rate TXRATE ]
                 [ spoofchk { on | off } ]
                 [ query_rss { on | off } ]
                 [ state { auto | enable | disable } ]
                 [ trust { on | off } ] ]
        [ master DEVICE ]
        [ nomaster ]
        [ addrgenmode { eui64 | none } ]

ip link show [ DEVICE ]
```

支持的设备type：
```
       TYPE := [ bridge | bond | can | dummy | ifb | ipoib | macvlan | macvtap | vcan | veth | vlan | vxlan | ip6tnl
               | ipip | sit | gre | gretap | ip6gre | ip6gretap | vti | nlmon | geneve | macsec ]

       ETYPE := [ TYPE | bridge_slave | bond_slave ]


                      bridge - Ethernet Bridge device

                      bond - Bonding device

                      dummy - Dummy network interface

                      ifb - Intermediate Functional Block device

                      ipoib - IP over Infiniband device

                      macvlan - Virtual interface base on link layer address (MAC)

                      macvtap - Virtual interface based on link layer address (MAC) and TAP.

                      vcan - Virtual Controller Area Network interface

                      veth - Virtual ethernet interface

                      vlan - 802.1q tagged virtual LAN interface

                      vxlan - Virtual eXtended LAN

                      ip6tnl - Virtual tunnel interface IPv4|IPv6 over IPv6

                      ipip - Virtual tunnel interface IPv4 over IPv4

                      sit - Virtual tunnel interface IPv6 over IPv4

                      gre - Virtual tunnel interface GRE over IPv4

                      gretap - Virtual L2 tunnel interface GRE over IPv4

                      ip6gre - Virtual tunnel interface GRE over IPv6

                      ip6gretap - Virtual L2 tunnel interface GRE over IPv6

                      vti - Virtual tunnel interface

                      nlmon - Netlink monitoring device

                      geneve - GEneric NEtwork Virtualization Encapsulation

                      macsec - Interface for IEEE 802.1AE MAC Security (MACsec)
```


## 显示设备、统计

显示所有设备
```sh
[root@host143 ~]# ip link show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: ens192: <BROADCAST,MULTICAST,PROMISC,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 00:50:56:b0:b8:fd brd ff:ff:ff:ff:ff:ff
```

LOWER-UP: L1是启动的，即网线是插着的。
>IFF_LOWER_UP      Driver signals L1 up (since Linux 2.6.17)


一些字段说明：

1. qdisc
QDisc(排队规则)是queueing discipline的简写，它是理解流量控制(traffic control)的基础。
内核如果需要通过某个网络接口发送数据包，它都需要按照为这个接口配置的qdisc(排队规则)把数据包加入队列。然后，内核会尽可能多地从qdisc里面取出数据包，把它们交给网络适配器驱动模块。
TOOD：以后再单独深入qdisc。

2. state（主要是UNKOWN）
>This can be DOWN (the network interface is not operational), 
>UNKNOWN (the network interface is operational but nothing is connected), 
>or UP (the network is operational and there is a connection)

3. qlen
最大传输队列长度


显示指定设备
```sh
[root@host143 ~]# ip link show ens192
2: ens192: <BROADCAST,MULTICAST,PROMISC,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 00:50:56:b0:b8:fd brd ff:ff:ff:ff:ff:ff
```

显示指定类型设备
```sh
[root@host143 ~]# ip link show type veth
279: veth964027a@if278: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-87716e5dd46e state UP mode DEFAULT group default 
    link/ether ee:9d:49:30:fe:32 brd ff:ff:ff:ff:ff:ff link-netnsid 0
```

显示统计，使用`-s`参数
```sh
[root@host143 ~]# ip -s link show ens192
2: ens192: <BROADCAST,MULTICAST,PROMISC,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    link/ether 00:50:56:b0:b8:fd brd ff:ff:ff:ff:ff:ff
    RX: bytes  packets  errors  dropped overrun mcast   
    93515409047 1076693605 0       206749  0       11621833 
    TX: bytes  packets  errors  dropped carrier collsns 
    77671901798 762758900 0       0       0       0 
```

## 启动/停止设备

`ip link set <device> {up|down}`
```sh
[root@host143 ~]# ip link show br-87716e5dd46e 
261: br-87716e5dd46e: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default 
    link/ether 02:42:62:ef:9a:d1 brd ff:ff:ff:ff:ff:ff

[root@host143 ~]# ip link set br-87716e5dd46e down

[root@host143 ~]# ip link show br-87716e5dd46e 
261: br-87716e5dd46e: <BROADCAST,MULTICAST> mtu 1500 qdisc noqueue state DOWN mode DEFAULT group default 
    link/ether 02:42:62:ef:9a:d1 brd ff:ff:ff:ff:ff:ff

[root@host143 ~]# ip link set br-87716e5dd46e up

[root@host143 ~]# ip link show br-87716e5dd46e 
261: br-87716e5dd46e: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default 
    link/ether 02:42:62:ef:9a:d1 brd ff:ff:ff:ff:ff:ff
```

## 增加/删除设备

```
ip link add [ link DEVICE ] [ name ] NAME
        [ txqueuelen PACKETS ]
        [ address LLADDR ] [ broadcast LLADDR ]
        [ mtu MTU ]
        [ numtxqueues QUEUE_COUNT ] [ numrxqueues QUEUE_COUNT ]
        type TYPE [ ARGS ]

ip link delete { DEVICE | group GROUP } type TYPE [ ARGS ]
```

```sh
[root@host143 ~]# ip link add veth0 type veth peer name veth1
[root@host143 ~]# ip link show type veth
314: veth1@veth0: <BROADCAST,MULTICAST,M-DOWN> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 7e:df:bd:e5:05:72 brd ff:ff:ff:ff:ff:ff
315: veth0@veth1: <BROADCAST,MULTICAST,M-DOWN> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 6e:3d:10:37:9a:9a brd ff:ff:ff:ff:ff:ff

```
veth设备总是成对出现。
没找到M-DOWN的意义。

删除其中一个veth设备，则peer也被自动删除：
```sh
[root@host143 ~]# ip link delete veth0
[root@host143 ~]# ip link show type veth
```

# ip addr

## 显示设备的ip地址

```sh
[root@host143 ~]# ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens192: <BROADCAST,MULTICAST,PROMISC,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:b0:b8:fd brd ff:ff:ff:ff:ff:ff
    inet 172.25.20.143/22 brd 172.25.23.255 scope global ens192
       valid_lft forever preferred_lft forever
    inet6 fe80::250:56ff:feb0:b8fd/64 scope link 
       valid_lft forever preferred_lft forever
```

## 分配新的ip地址

```sh
[root@host143 ~]# ip addr add 172.25.20.100 dev ens192 label ens192:100
[root@host143 ~]# ip addr show ens192
2: ens192: <BROADCAST,MULTICAST,PROMISC,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:b0:b8:fd brd ff:ff:ff:ff:ff:ff
    inet 172.25.20.143/22 brd 172.25.23.255 scope global ens192
       valid_lft forever preferred_lft forever
    inet 172.25.20.100/32 scope global ens192:100
       valid_lft forever preferred_lft forever
    inet6 fe80::250:56ff:feb0:b8fd/64 scope link 
       valid_lft forever preferred_lft forever
```
`label`是别名。

1. scope
scope默认是global。选项有：
- global ：允许来自所有来源的连线
- site   ：仅支持IPv6 ，仅允许本主机的连接
- link   ：仅允许本设备自我连接
- host   ：仅允许本主机内部的连接

关于site，只支持ipv6：
>Site-local address are supposed to be used within a site. 
>Routers will not forward any packet with site-local source or destination address outside the site.

关于link：
>Link-local address are supposed to be used for addressing nodes on a single link. 
>Packets originating from or destined to a link-local address will not be forwarded by a router.

2. 两个lft
```
valid_lft = Valid Lifetime            地址的有效使用期限
preferred_lft = Preferred Lifetime    地址的首选生存期
```

3. 也可以使用ifconfig查看
```sh
[root@host143 ~]# ifconfig ens192:100
ens192:100: flags=4419<UP,BROADCAST,RUNNING,PROMISC,MULTICAST>  mtu 1500
        inet 172.25.20.100  netmask 255.255.255.255  broadcast 0.0.0.0
        ether 00:50:56:b0:b8:fd  txqueuelen 1000  (Ethernet)
```

## 删除ip地址

```sh
[root@host143 ~]# ip addr delete 172.25.20.100 dev ens192:100
Warning: Executing wildcard deletion to stay compatible with old scripts.
         Explicitly specify the prefix length (172.25.20.100/32) to avoid this warning.
         This special behaviour is likely to disappear in further releases,
         fix your scripts!

# 已经释放172.25.20.100
[root@host143 ~]# ip addr show ens192
2: ens192: <BROADCAST,MULTICAST,PROMISC,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:b0:b8:fd brd ff:ff:ff:ff:ff:ff
    inet 172.25.20.143/22 brd 172.25.23.255 scope global ens192
       valid_lft forever preferred_lft forever
    inet6 fe80::250:56ff:feb0:b8fd/64 scope link 
       valid_lft forever preferred_lft forever
```

# ip netns

先啰嗦下网络名空间：
>A network namespace is logically another copy of the network stack,
>with its own routes, firewall rules, and network devices.
>
>By default a process inherits its network namespace from its parent.
>Initially all the processes share the same default network namespace
>from the init process.

每个新的network namespace默认有一个本地环回接口，除了lo接口外，所有的其他网络设备（物理/虚拟网络接口，网桥等）只能属于一个network namespace。每个socket也只能属于一个network namespace。

## 查看、添加、删除netns

```sh
[root@host143 ~]# ip netns add ns1
[root@host143 ~]# ip netns add ns2

[root@host143 ~]# ip netns 
ns2
ns1

[root@host143 ~]# ip netns delete ns1
[root@host143 ~]# ip netns delete ns2
[root@host143 ~]# ip netns 
```

netns会在`/var/run/netns/`创建文件
```sh
[root@host143 ~]# ls -al /var/run/netns/
总用量 0
drwxr-xr-x  2 root root   80 6月  18 16:12 .
drwxr-xr-x 45 root root 1380 6月  18 06:50 ..
-r--r--r--  1 root root    0 6月  18 15:57 ns1
-r--r--r--  1 root root    0 6月  18 15:57 ns2
```

## exec 在指定netns运行程序

上面提到，新建的netns会自带lo设备，并且处于关闭状态：
```sh
[root@host143 ~]# ip netns exec ns1 ip link
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
```

因为lo没有起来，ping不通本地地址
```sh
[root@host143 ~]# ip netns exec ns1 ping 127.0.0.1
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
^C
--- 127.0.0.1 ping statistics ---
5 packets transmitted, 0 received, 100% packet loss, time 3999ms
```

exec后面可以执行任意合法的程序，比如bash。

## pids 查看指定netns下面有哪些进程pid

```sh
# 第一个shell窗口
[root@host143 ~]# ip netns exec ns1 sleep 100

# 第二个shell窗口
[root@host143 ~]# ip netns pids ns1
91560

[root@host143 ~]# ps aux | grep 91560
root      91560  0.0  0.0 107956   616 pts/2    S+   16:04   0:00 sleep 100
root      93332  0.0  0.0 112732   972 pts/1    S+   16:06   0:00 grep --color=auto 91560
```

## monitor 监控netns的add/delete事件

| shell 1                                | shell 2                               |
| -------------------------------------- | ------------------------------------- |
| [root@host143 ~]# ip netns monitor ns3 |                                       |
|                                        | [root@host143 ~]# ip netns add ns3    |
| add ns3                                |                                       |
|                                        | [root@host143 ~]# ip netns delete ns3 |
| delete ns3                             |                                       |


## 连接两个netns

```sh
# 创建2个netns
[root@host143 ~]# ip netns add ns1
[root@host143 ~]# ip netns add ns2

# 启动netns的lo设备
[root@host143 ~]# ip netns exec ns1 ip link set dev lo up
# 因为没有分配ip，所以是UNKOWN状态
[root@host143 ~]# ip netns exec ns1 ip link 
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
# 可以ping通localhost
[root@host143 ~]# ip netns exec ns1 ping 127.0.0.1
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.030 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.045 ms
^C
--- 127.0.0.1 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 999ms
rtt min/avg/max/mdev = 0.030/0.037/0.045/0.009 ms

[root@host143 ~]# ip netns exec ns2 ip link set dev lo up

# 创建veth pair
[root@host143 ~]# ip link add veth0 type veth peer name veth1
# 切换netns
[root@host143 ~]# ip link set dev veth0 netns ns1
[root@host143 ~]# ip link set dev veth1 netns ns2

# ns1中已经增加veth0设备
[root@host143 ~]# ip netns exec ns1 ip link
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
317: veth0@if316: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether c6:dc:57:6a:cd:9c brd ff:ff:ff:ff:ff:ff link-netnsid 1
# 启动veth
[root@host143 ~]# ip netns exec ns1 ip link set dev veth0 up
[root@host143 ~]# ip netns exec ns1 ip link
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
317: veth0@if316: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state LOWERLAYERDOWN mode DEFAULT group default qlen 1000
    link/ether c6:dc:57:6a:cd:9c brd ff:ff:ff:ff:ff:ff link-netnsid 1

[root@host143 ~]# ip netns exec ns2 ip link set dev veth1 up    


# 分配ip地址
[root@host143 ~]# ip netns exec ns1 ip addr add dev veth0 192.168.1.10/24
[root@host143 ~]# ip netns exec ns2 ip addr add dev veth1 192.168.1.20/24

# ns1 联通 ns2
[root@host143 ~]# ip netns exec ns1 ping 192.168.1.20
PING 192.168.1.20 (192.168.1.20) 56(84) bytes of data.
64 bytes from 192.168.1.20: icmp_seq=1 ttl=64 time=0.090 ms
64 bytes from 192.168.1.20: icmp_seq=2 ttl=64 time=0.030 ms
64 bytes from 192.168.1.20: icmp_seq=3 ttl=64 time=0.034 ms
^C
--- 192.168.1.20 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2000ms
rtt min/avg/max/mdev = 0.030/0.051/0.090/0.028 ms
```

一个设备只能属于一个 Network Namespace。如果转移了netns，那么在原来netns就看不到该设备了。


# ip route 

```sh
[root@host143 ~]# ip route 
default via 172.25.23.254 dev ens192 
169.254.0.0/16 dev ens192 scope link metric 1002 
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 
172.21.0.0/16 dev br-87716e5dd46e proto kernel scope link src 172.21.0.1 
172.25.20.0/22 dev ens192 proto kernel scope link src 172.25.20.143 
192.168.122.0/24 dev virbr0 proto kernel scope link src 192.168.122.1
```

1. scope定义和上面`ip addr`一样。
link表示连接到本设备

2. metric
路由距离，到达指定网络所需的中转数

3. proto：路由协议。可以是数字或者字符串，保存在`/etc/iproute2/rt_protos`
```sh
[root@host143 ~]# cat /etc/iproute2/rt_protos
#
# Reserved protocols.
#
0	unspec
1	redirect
2	kernel
3	boot
4	static
8	gated
9	ra
10	mrt
11	zebra
12	bird
13	dnrouted
14	xorp
15	ntk
16      dhcp
42	babel

#
#	Used by me for gated
#
254	gated/aggr
253	gated/bgp
252	gated/ospf
251	gated/ospfase
250	gated/rip
249	gated/static
248	gated/conn
247	gated/inet
246	gated/default
```

常见的proto有：
>redirect - the route was installed due to an ICMP redirect.
>kernel - the route was installed by the kernel during autoconfiguration.
>boot - the route was installed during the bootup sequence. If a routing daemon starts, it will purge all of them.
>static - the route was installed by the administrator to override dynamic routing. Routing daemon will respect them and, probably, even advertise them to its peers.
>ra - the route was installed by Router Discovery protocol.

4. 也可以使用route命令
```sh
[root@host143 ~]# route
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
default         gateway         0.0.0.0         UG    0      0        0 ens192
link-local      0.0.0.0         255.255.0.0     U     1002   0        0 ens192
172.17.0.0      0.0.0.0         255.255.0.0     U     0      0        0 docker0
172.21.0.0      0.0.0.0         255.255.0.0     U     0      0        0 br-87716e5dd46e
172.25.20.0     0.0.0.0         255.255.252.0   U     0      0        0 ens192
192.168.122.0   0.0.0.0         255.255.255.0   U     0      0        0 virbr0

```

Flags标记。一些可能的标记如下：
> 	U — 路由是活动的
> 	H — 目标是一个主机
> 	G — 路由指向网关
> 	R — 恢复动态路由产生的表项
> 	D — 由路由的后台程序动态地安装
> 	M — 由路由的后台程序修改
> 	! — 拒绝路由

TODO：以后再补充其他路由操作

# ip neighbor

TODO

# 参考

- [ip-link.html](https://www.linux.org/docs/man8/ip-link.html)
- [netdevice.7.html](https://man7.org/linux/man-pages/man7/netdevice.7.html)
- [ip-address-scope-parameter](https://serverfault.com/questions/63014/ip-address-scope-parameter)
- [Linux Namespace系列（06）：network namespace (CLONE_NEWNET)](https://segmentfault.com/a/1190000006912930)
