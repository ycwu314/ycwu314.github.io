---
title: linux namespace 简介
date: 2019-10-03 20:47:32
tags: [linux]
categories: [linux]
keywords: [linux namespace]
description: 整理一些linux namespace的资料。
---

# linux namespace

Linux Namespace 是linux内核在不同进程间实现的一种**环境隔离机制**。
Linux 内核实现 namespace 的一个主要目的就是实现轻量级虚拟化(容器)服务。在同一个 namespace 下的进程可以感知彼此的变化，而对外界的进程一无所知。
<!-- more -->
Linux 一共构建了 6 种不同的 Namespace，用于不同场景下的隔离：
- Mount - isolate filesystem mount points
- UTS - isolate hostname and domainname
- IPC - isolate interprocess communication (IPC) resources
- PID - isolate the PID number space
- Network - isolate network interfaces
- User - isolate UID/GID number spaces

主要是三个系统调用
- clone() – 实现线程的系统调用，用来创建一个新的进程，并可以通过设计上述参数达到隔离
- unshare() – 使某进程脱离某个namespace
- setns() – 把某进程加入到某个namespace

具体的例子参见陈老师的文章：[DOCKER基础技术：LINUX NAMESPACE（上）](https://coolshell.cn/articles/17010.html)。

# UTS Namespace

UTS: UNIX Time-sharing System。
UTS namespace用来隔离系统的hostname以及NIS domain name。
hostname 是用来标识一台主机的。

NIS（Network Information Service）来自wiki的介绍
>The Network Information Service, or NIS (originally called Yellow Pages or YP), is a client–server directory service protocol for distributing system configuration data such as user and host names between computers on a computer network.

就是一台账号主控服务器来管理网络中所有主机的账号，当其他的主机有用户登入的需求时，才到这部主控服务器上面请求相关的账号、密码等用户信息， 如此一来，如果想要增加、修改、删除用户数据，只要到这部主控服务器上面处理即可。

UTS namespace没有嵌套关系。

# IPC Namespace

IPC全称 Inter-Process Communication，是Unix/Linux下进程间通信的一种方式，IPC有共享内存、信号量、消息队列等方法。
IPC Namespace 只有在同一个Namespace下的进程才能相互通信。

# PID Namespace

PID namespaces用来隔离进程的ID空间，使得不同pid namespace里的进程ID可以重复且相互之间不影响。
PID namespace可以嵌套，也就是说有父子关系，在当前namespace里面创建的所有新的namespace都是当前namespace的子namespace。
每个PID namespace的第一个进程的ID都是1。

在linux系统种，PID为1的进程是init。init进程，它是一个由内核启动的用户级进程。当系统中一个进程的父进程退出时，内核会指定init进程成为这个进程的新父进程，而当init进程退出时，系统也将退出。因此内核会帮init进程屏蔽掉其他任何信号，这样可以防止其他进程不小心kill掉init进程导致系统挂掉。

PID namesapce 对容器类应用特别重要， 可以实现容器内进程的暂停/恢复等功能，还可以支持容器在跨主机的迁移前后保持内部进程的 PID 不发生变化。

# Mount Namespace

Mount namespace用来隔离文件系统的挂载点, 使得不同的mount namespace拥有自己独立的挂载点信息，不同的namespace之间不会相互影响。
当前进程所在mount namespace里的所有挂载信息可以在这些路径找到：
- /proc/[pid]/mounts
- /proc/[pid]/mountinfo
- /proc/[pid]/mountstats

有另一个场景，需要一个mount point在各个namespace共享。由于mount namespace是隔离的，以前的做法是，在各个mount namespace都执行一次挂载，才可以访问共享的mount point。
Shared subtree 允许在 mount namespace 之间自动地或者是受控地传播 mount 和 umount 事件。

# Network Namespace

Network namespace 在逻辑上是网络堆栈的一个副本，它有自己的路由、防火墙规则和网络设备。
Network namespace 之间是相互隔离的，我们可以使用 veth 设备把两个 network namespace 连接起来进行通信。veth 设备是虚拟的以太网设备。它们可以充当 network namespace 之间的通道，也可以作为独立的网络设备使用。
ip netns 命令用来管理 network namespace。

# User Namespace

User namespace 是 Linux 3.8 新增的一种 namespace，用于隔离安全相关的资源。
一个用户可以在一个 user namespace 中是普通用户，但在另一个 user namespace 中是超级用户。
User namespace 可以嵌套。

# todo

unshare和ip netns命令的实验。

# 参考

- [Linux Namespace : PID](https://www.cnblogs.com/sparkdev/p/9442208.html)
- [Linux Namespace : Mount](https://www.cnblogs.com/sparkdev/p/9424649.html)
- [Linux Namespace : User](https://www.cnblogs.com/sparkdev/p/9462838.html)
