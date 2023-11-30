---
title: "Linux utmp wtmp btmp文件"
date: 2023-11-09T11:36:28+08:00
tags: [linux]
categories: [linux]
description: utmp、wtmp 和 btmp 都是二进制文件，用于记录 Linux 系统上的登录、注销和登录尝试。
---

小鸡磁盘要写满，留意到`/var/log/btmp`文件比较大。顺便做下了解。

utmp、wtmp 和 btmp 都是二进制文件，用于记录 Linux 系统上的登录、注销和登录尝试。

# utmp、wtmp、btmp

1. utmp

u代表用户，记录有关“谁”登录系统的信息。

2. wtmp

w代表who和when，记录谁以及“何时”登录和注销。

3. btmp

b代表bad，记录了所有错误、失败或错误的登录尝试。


# 相关命令

## last

last显示用户历史登录情况。访问`/var/log/utmp`文件。

```
root@vm513254:/var/log# last | head
root     pts/1        113.108.130.106  Thu Nov  9 11:19   still logged in
root     pts/0        113.108.130.106  Thu Nov  9 11:16   still logged in
root     pts/0        120.239.180.42   Sat Oct 28 11:45 - 11:46  (00:00)
root     pts/0        120.239.180.42   Sat Oct 28 11:24 - 11:24  (00:00)
```

## lastb

lastb查看失败登录尝试的历史记录。访问`/var/log/btmp`文件。

```
root@vm513254:/var/log# lastb | head
yz       ssh:notty    66.70.178.149    Thu Nov  9 12:26 - 12:26  (00:00)
admin    ssh:notty    59.14.37.194     Thu Nov  9 12:26 - 12:26  (00:00)
yz       ssh:notty    66.70.178.149    Thu Nov  9 12:26 - 12:26  (00:00)
```


统计恶意ip试图登录次数：
```
lastb | awk '{ print $3}' | sort | uniq -c | sort -n
```

## w

>w - displays information about the users currently on the machine, and their processes. 

w访问`/var/run/utmp`。

```
root@vm513254:/var/log# w
 12:23:55 up 97 days, 23:49,  2 users,  load average: 0.28, 0.08, 0.02
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    113.108.130.106  11:16    1:04m  4.88s  4.79s ncdu
root     pts/1    113.108.130.106  11:19    1.00s  0.18s  0.01s w

```