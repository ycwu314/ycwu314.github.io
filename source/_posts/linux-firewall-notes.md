---
title: 防火墙概念笔记
date: 2020-05-20 16:49:33
tags: [linux]
categories: [linux]
keywords: [有状态防火墙, 无状态防火墙, conntrack]
description: 
---

整理的学习防火墙笔记。
<!-- more -->

# 概念

>无状态防火墙就是基于静态数值来过滤或阻拦网络数据包。例如基于地址，端口，协议等等。无状态指的就是，防火墙本身不关心当前的网络连接状态。
>
>有状态防火墙能区分出网络连接的状态。例如TCP连接，有状态防火墙可以知道当前是连接的哪个阶段。也就是说，有状态防火墙可以在静态数值之外，再通过连接状态来过滤或阻拦网络数据包。

无状态防火墙只进行地址，端口，协议等规则匹配，实现比较简单，消耗资源较少，也可以做成硬件进一步加速。适用于负载很高、规则简单的场景。

无状态防火墙的不足：
- 如果规则很多，则检索表（lookup table）就会很大，交换机、路由器等内存有限的硬件会很敏感
- 大规模部署，管理这些规则也是问题
- 没有充分利用连接的上下文信息

# ct状态机

网络连接的状态，通常是由connection tracker来实现。可以简称为CT模块。在linux内核中，CT是由conntrack实现，其内部实际上是对各个网络连接实现了状态机。
**CT状态机跟具体通信协议无关**。

CT状态机管理的connection，有2个关注点：
- 怎样才算建立了连接?
- 怎样才算连接断开？

对于建立连接：
- 只要是第一个packet，就认为connection是NEW，收到了第一个合法的返回，就认为connection是ESTABLISHED。

对于连接断开：
- 依赖connection的TTL。

（以下几张图片来源于参考文章）

1. tcp
{% asset_img ct_tcp.jpg  %}
收到SYN/ACK就认为connection是ESTABLISHED。

```sh
[root@host143 ~]# conntrack -L -p tcp -f ipv4 --dport 3306 -o timestamp
tcp      6 431915 ESTABLISHED src=172.25.21.29 dst=172.25.20.143 sport=57764 dport=3306 src=172.25.20.143 dst=172.25.21.29 sport=3306 dport=57764 [ASSURED] mark=0 use=1
```

2. udp
{% asset_img ct_udp.jpg  %}
第一个UDP包创建的NEW状态的UDP connection，TTL是30；当connection变成ESTABLISHED，其TTL默认值是180。
```sh
[root@host143 ~]# conntrack -L -p udp -f ipv4 -o timestamp
udp      17 5 src=172.25.23.15 dst=255.255.255.255 sport=46705 dport=1947 [UNREPLIED] src=255.255.255.255 dst=172.25.23.15 sport=1947 dport=46705 mark=0 use=1
```

3. icmp
icmp不熟悉，以后再补充。
{% asset_img ct_icmp.jpg  %}

```sh
[root@host143 ~]# conntrack -L -p icmp -f ipv4 -o timestamp
icmp     1 28 src=172.28.51.6 dst=172.25.20.143 type=8 code=0 id=3 src=172.25.20.143 dst=172.28.51.6 type=0 code=0 id=3 mark=0 use=1
```

# 参考

- [Stateful firewall in OpenFlow based SDN](https://zhuanlan.zhihu.com/p/25089778)