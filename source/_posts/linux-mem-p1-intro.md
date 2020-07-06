---
title: linux内存系列1：基本概念和工具
date: 2020-07-02 15:23:50
tags: [linux]
categories: [linux]
keywords: [linux meminfo, linux buff cache, vmstat ]
description: /proc/meminfo包含机器级别内存使用清空。
---

linux内存相关比较复杂。我们从常见命令开始入手，逐步理解linux内存设计和管理。
<!-- more -->

# free命令

free命令可以简单看到机器整体内存情况。
free从`/proc/meminfo`读取信息。
```sh
# 默认是kb
# -h：以人类友好的方式展示数据
[root@host143 ~]# free -h
              total        used        free      shared  buff/cache   available
Mem:            15G        737M         14G         12M        655M         14G
Swap:            0B          0B          0B
```

free输出的各个字段解释如下（来自`man free`）：
```
total  Total installed memory (MemTotal and SwapTotal in /proc/meminfo)

used   Used memory (calculated as total - free - buffers - cache)

free   Unused memory (MemFree and SwapFree in /proc/meminfo)

shared Memory used (mostly) by tmpfs (Shmem in /proc/meminfo, available on kernels 2.6.32, displayed as zero if not available)

buffers
       Memory used by kernel buffers (Buffers in /proc/meminfo)

cache  Memory used by the page cache and slabs (Cached and SReclaimable in /proc/meminfo)

buff/cache
        Sum of buffers and cache

available
        Estimation of how much memory is available for starting new applications, withouswapping. Unlike the data provided  by  the  cache  or  free
        fields,  this  field  takes into account page cache and also that not all reclaimablmemory slabs will be reclaimed due to items being in use
        (MemAvailable in /proc/meminfo, available on kernels 3.14, emulated on kernels 2.6.27+otherwise the same as free)
```

## buff / cache

linux文件系统做了优化，使用大量的buff/cache缓存访问过的文件，二次读取速度很快。

buffers是块设备的缓冲区。
buffers主要用于缓存文件系统中的元数据信息(dentries、inodes)，和另外一些不是文件数据的块，例如metadata和raw block I/O。
cached包括page cache和SReclaimable。

在linux文件系统中，buffer加速对磁盘块的读写，page cache加速文件inode的读写。

这里扩展一下，
>dentry的是目录项，是Linux文件系统中某个索引节点(inode)的链接。这个索引节点可以是文件的，也可以是目录的。

大量使用buff/cache，会导致free字段看起来很少。但是buff和cache作为缓存是可以释放的。


## 手动清空caches

99.99%的情况下，都没有必要去手动清理caches，交给linux内存管理就好。
有些场景可能需要，比如 IO benchmark。

>file: /proc/sys/vm/drop_caches
>variable: vm.drop_caches


```sh
# 清理pagecache（页面缓存）
# sysctl -w vm.drop_caches=1
[root@localhost ~]# echo 1 > /proc/sys/vm/drop_caches     
 
# 清理dentries（目录缓存）和inodes
# sysctl -w vm.drop_caches=2
[root@localhost ~]# echo 2 > /proc/sys/vm/drop_caches   
 
# 清理pagecache、dentries和inodes
# sysctl -w vm.drop_caches=3
[root@localhost ~]# echo 3 > /proc/sys/vm/drop_caches     

```
  
## available

通常关注的是`available`字段：
>Estimation of how much memory is available for starting new applications, without swapping. 

available是估算值，大致为
```
available = free + (buff/cache 可以回收的部分)
```


# top命令，ps命令

top命令能够进程级别的内存使用情况。
```
Tasks:   1 total,   0 running,   1 sleeping,   0 stopped,   0 zombie
%Cpu(s):  0.1 us,  0.1 sy,  0.0 ni, 99.8 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
KiB Mem : 16249876 total, 14795000 free,   777544 used,   677332 buff/cache
KiB Swap:        0 total,        0 free,        0 used. 15183136 avail Mem 

   PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND                                                                                   
     1 root      20   0  191164   4200   2584 S   0.0  0.0   0:05.34 systemd
```

从centos 7.5的`man top`截取字段介绍：
```
 4. CODE  --  Code Size (KiB)
    The amount of physical memory devoted to executable code, also known as the Text Resident Set size or TRS.

 6. DATA  --  Data + Stack Size (KiB)
    The amount of physical memory devoted to other than executable code, also known as the Data Resident Set size or DRS.

17. RES  --  Resident Memory Size (KiB)
    The non-swapped physical memory a task is using.
    （占用的物理内存，不包括swap，包括共享内存和私有内存）
    （对应ps命令的RSS）

21. SHR  --  Shared Memory Size (KiB)
    The  amount  of  shared  memory available to a task, not all of which is typically resident.  It simply reflects memory that could be potentially
    shared with other processes.

27. SWAP  --  Swapped Size (KiB)
    The non-resident portion of a task's address space.

34. USED  --  Memory in Use (KiB)
    This field represents the non-swapped physical memory a task has used (RES) plus the non-resident portion of its address space (SWAP).

36. VIRT  --  Virtual Memory Size (KiB)
    The  total  amount of virtual memory used by the task.  It includes all code, data and shared libraries plus pages that have been swapped out and
    pages that have been mapped but not used.
```

ps命令也可以看到进程级别的内存情况：
```sh
[root@host143 ~]# ps axu | head 
USER        PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root          1  0.0  0.0 191324  3416 ?        Ss   3月23  27:29 /usr/lib/systemd/systemd --switched-root --system --deserialize 22
```

top和ps都能修改显示的列，这里就不展开了。

## RSS和RES

top命令的`%MEM`列显示的是RES内存使用率。

top命令的`RES`对应于ps命令的`RSS`（RSS是常驻内存集（Resident Set Size））。
两者都是读取`/proc/$(pidof process)/status`。

## VIRT

top命令的`VIRT`对应于ps命令的`VSZ`。 
VSZ包括进程可以访问的所有内存，包括进入交换分区的内容，以及共享库占用的内存。

## SHR和PSS

SHR内存被多个进程共享，可能导致各个进程加起来（RSS+SHR）比物理内存还要大。

因为SHR会被反复计算，因此引入了PSS内存的概念：
>PSS = SHR / (共享这份SHR的进程数)
>The "proportional set size" (PSS) of a process is the count of pages it has in memory, where each page is divided by the number of processes sharing it.
>So if a process has 1000 pages all to itself, and 1000 shared with one other process, its PSS will be 1500

另外，线程共享同一个地址空间，所以一个进程内部的所有线程有相同的RSS，VSZ和PSS。

## 小结

内存方面，top主要关注RES，ps关注RSS。

# vmstat

`vmstat -s`查看统计。数据同样来自`/proc/meminfo`。
```sh
[root@localhost ~]# vmstat -s
     16247672 K total memory
      1338220 K used memory
# 这里增加了active和inactive，后面再展开
      2231860 K active memory
      1760584 K inactive memory
     11842600 K free memory
         2660 K buffer memory
      3064192 K swap cache
      1679356 K total swap
            0 K used swap
      1679356 K free swap
       420031 non-nice user cpu ticks
          264 nice user cpu ticks
       440930 system cpu ticks
    743674626 idle cpu ticks
        59055 IO-wait cpu ticks
            0 IRQ cpu ticks
        49343 softirq cpu ticks
            0 stolen cpu ticks
       259860 pages paged in
      5564186 pages paged out
            0 pages swapped in
            0 pages swapped out
   1136970454 interrupts
    815767131 CPU context switches
   1591807821 boot time
      2345107 forks
```

# /proc/meminfo 文件

`/proc/meminfo`查看机器的内存（物理、虚拟）情况，是free、vmstat等工具的数据来源。
信息很多，持续更新。
```sh
[root@localhost ~]# cat /proc/meminfo
# 物理内存减去内核预留内存之后的总内存
MemTotal:       16247672 kB
# 未被使用的内存
MemFree:        11843704 kB
# MemFree加上cache/buffer、slab可以回收部分
MemAvailable:   14567188 kB

# buffers是块设备的缓冲区。
# buffers主要用于缓存文件系统中的元数据信息(dentries、inodes)，和另外一些不是文件数据的块，例如metadata和raw block I/O
# cached包括page cache和SReclaimable的slab （来自free的说明）
Buffers:            2660 kB
Cached:          2925600 kB
SwapCached:            0 kB

# page cache相关
# Active Memory等于ACTIVE_ANON与ACTIVE_FILE之和
# Inactive Memory等于INACTIVE_ANON与INACTIVE_FILE之和
Active:          2230508 kB
Inactive:        1761472 kB
Active(anon):    1064524 kB
Inactive(anon):    19424 kB
Active(file):    1165984 kB
Inactive(file):  1742048 kB

# 不能pageout/swapout的内存页，包括VM_LOCKED的内存页、SHM_LOCK的共享内存页
Unevictable:           0 kB
# 被mlock()系统调用锁定的内存大小。
# 被锁定的内存因为不能pageout/swapout，会从Active/Inactive LRU list移到Unevictable LRU list上
# “Mlocked”并不是独立的内存空间，它与以下统计项重叠：LRU Unevictable，AnonPages，Shmem，Mapped等。
Mlocked:               0 kB

SwapTotal:       1679356 kB
SwapFree:        1679356 kB

# 等待被写回到磁盘的内存大小
Dirty:                60 kB
# 正在被写回的大小
Writeback:             0 kB

# 未映射的页的大小
AnonPages:       1063740 kB
Mapped:            52360 kB
# 共享页大小
Shmem:             20228 kB

# 内核数据结构缓存的大小
Slab:             215648 kB
# 可以回收的slab
SReclaimable:     138316 kB
# 不可以回收的slab
SUnreclaim:        77332 kB
KernelStack:        5232 kB
PageTables:         8856 kB
# NFS相关
NFS_Unstable:          0 kB

# ??
Bounce:                0 kB
WritebackTmp:          0 kB
CommitLimit:     9803192 kB
Committed_AS:    2764260 kB

VmallocTotal:   34359738367 kB
VmallocUsed:      206204 kB
VmallocChunk:   34359310332 kB
HardwareCorrupted:     0 kB
AnonHugePages:    909312 kB
CmaTotal:              0 kB
CmaFree:               0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
DirectMap4k:      173888 kB
DirectMap2M:     8214528 kB
DirectMap1G:    10485760 kB
```


# 参考

- [/PROC/MEMINFO之谜](http://linuxperf.com/?cat=7)