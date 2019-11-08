---
title: redis "Can't open PID file" 经历
date: 2019-11-08 11:45:46
tags: [redis, 故障案例]
categories: [故障案例]
keywords: [redis ipv6, redis cant open pid file]
description: redis默认支持绑定IPv6地址，如果主机没有分配IPv6地址，会导致启动报错："Can't open PID file"。
---

在ubuntu上使用apt安装redis报错。
<!-- more -->
```
Job for redis-server.service failed because a timeout was exceeded.
See "systemctl status redis-server.service" and "journalctl -xe" for details.
invoke-rc.d: initscript redis-server, action "start" failed.
● redis-server.service - Advanced key-value store
   Loaded: loaded (/lib/systemd/system/redis-server.service; disabled; vendor preset: enabled)
   Active: activating (auto-restart) (Result: timeout) since Mon 2019-11-04 15:42:39 CST; 6ms ago
     Docs: http://redis.io/documentation,
           man:redis-server(1)

Nov 04 15:42:39 VM-0-2-ubuntu systemd[1]: Failed to start Advanced key-value store.
dpkg: error processing package redis-server (--configure):
 installed redis-server package post-installation script subprocess returned error exit status 1
Errors were encountered while processing:
 redis-server
E: Sub-process /usr/bin/dpkg returned an error code (1)
```

于是查看服务状态
```
# systemctl status redis-server.service

Nov 04 15:42:39 VM-0-2-ubuntu systemd[1]: Starting Advanced key-value store...
Nov 04 15:42:39 VM-0-2-ubuntu systemd[1]: redis-server.service: Can't open PID file /var/run/redis
```
以为是权限问题，使用sudo启动，依然如此。
嗯，这个报错信息没卵用。网上搜到类似情况，是redis默认支持IPv6地址，但是主机没有，导致报错。

打开redis.conf，发现
>bind 127.0.0.1 ::1

`::1`是IPv6的loopback地址，对应IPv4的`127.0.0.1`。
因为ecs没有分配IPv6网卡地址，绑定IPv6的loopback肯定报错。于是去掉`::1`。再次启动
```
sudo systemctl start redis-server.service
```
搞定。

思考：
- 虽然IPv6是大趋势，但是也不能默认选项就是listen v6地址，运行环境不一定有v6地址。
- 提示只有"Can't open PID file"，对发现问题没有帮助，引起误导。
