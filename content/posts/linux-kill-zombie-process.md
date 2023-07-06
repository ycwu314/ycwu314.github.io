---
title: 处理zombie进程
date: 2020-09-16 18:00:56
tags: [linux]
categories: [linux]
keywords: [linux zombie, ps defunct]
description:
---

登录vps后提示有僵尸进程，顺手处理掉。
<!-- more -->

```
  System load:  0.03               Processes:           120
  Usage of /:   59.4% of 49.15GB   Users logged in:     1
  Memory usage: 61%                IP address for eth0: 172.16.0.2
  Swap usage:   40%

  => There is 1 zombie process.
```

查找僵尸进程：
```
ubuntu@VM-0-2-ubuntu:~$ ps -ef | grep defunct
ubuntu     964   442  0 17:35 pts/1    00:00:00 grep --color=auto defunct
nobody    6392  1478  0 03:11 ?        00:00:00 [mvn] <defunct>
```

或者
```
ubuntu@VM-0-2-ubuntu:~$ ps -A -o stat,ppid,pid,cmd | grep -e '^[Zz]' 
Z     1478  6392 [mvn] <defunct>
```

检查僵尸进程
```
ubuntu@VM-0-2-ubuntu:~$ top -p 6392

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND                                                               
 6392 nobody    20   0       0      0      0 Z   0.0  0.0   0:00.00 mvn
```
注意state为Z。

顺便看下父进程状态
```
ubuntu@VM-0-2-ubuntu:~$ top -p 1478

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND                                                               
 1478 nobody    20   0    4628    376    372 T   0.0  0.0   0:00.36 mvn
```
注意state为T。

>Linux进程状态：T (TASK_STOPPED or TASK_TRACED)，暂停状态或跟踪状态。

清理僵尸进程方法是
- kill -9 <pid of zombie>
- 如果不行，则kill父进程

