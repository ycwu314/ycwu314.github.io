---
title: linux du df 命令
date: 2020-06-06 16:43:54
tags: [linux]
categories: [linux]
keywords: [linux du df]
description: du命令结合sort使用的例子。
---

一个常见的运维需求：看下当前目录的磁盘使用情况，并且排序。
<!-- more -->

du命令查看磁盘使用情况。
- `-h`：指定人类友好的输出，比如K、M、G等，而非以块为单位。
- `-d`：指定目录深度，不指定则递归遍历。

排序使用sort，没问题。因为du使用了`-h`选项，sort默认不能很好处理带单位的排序，比如1.4G和9M。
sort增加了`-h`，支持人类友好的易读性数字(例如： 2K 1G)排序（`-h  --human-numeric-sort`）。
```sh
[root@host143 ~]# du -hd 1 . | sort -hr
1.4G	.
517M	./project
246M	./frontend
136M	./.cache
123M	./standalone_143.etcd
78M	./logs
77M	./.pm2-dev
74M	./.pm2
73M	./go
59M	./.mozilla
11M	./.npm
1.5M	./.local
672K	./.ansible
132K	./nacos
112K	./.config
36K	./.vnc
16K	./.ssh
16K	./.dbus
12K	./.node-diamond-client-cache
4.0K	./.pip
4.0K	./.oracle_jre_usage、
```

df查看磁盘剩余空间，就不多说了。