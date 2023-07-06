---
title: linux内存系列3：匿名页和内存映射
date: 2020-07-06 19:35:22
tags: [linux]
categories: [linux]
keywords: [anon page, pmap, smaps]
description: 用户进程的内存页分为两种：file-backed pages（与文件对应的内存页），和anonymous pages（匿名页）。进程的堆、栈都是不与文件相对应的、就属于匿名页。
---

# anonymous pages

meminfo的active/inactive部分有file/anon，具体是什么呢？
<!-- more -->
```sh
[root@host143 ~]# cat /proc/meminfo
// 省略
Active:          3357056 kB
Inactive:         732448 kB
Active(anon):    2815280 kB
Inactive(anon):    11608 kB
Active(file):     541776 kB
Inactive(file):   720840 kB
```

>用户进程的内存页分为两种：file-backed pages（与文件对应的内存页），和anonymous pages（匿名页）。
>比如进程的代码、映射的文件都是file-backed。
>进程的堆、栈都是不与文件相对应的、就属于匿名页。
>
>file-backed pages在内存不足的时候可以直接写回对应的硬盘文件里，称为page-out，不需要用到交换区(swap)。
>而anonymous pages在内存不足时就只能写到硬盘上的交换区(swap)里，称为swap-out。


# pmap

pmap命令输出进程的内存映射情况。
```sh
# pmap [options] <pid>
[root@host143 ~]# pmap -dp 1
1:   /usr/lib/systemd/systemd --switched-root --system --deserialize 22
Address           Kbytes Mode  Offset           Device    Mapping
00005578ffecb000    1408 r-x-- 0000000000000000 0fd:00000 /usr/lib/systemd/systemd
000055790022a000     140 r---- 000000000015f000 0fd:00000 /usr/lib/systemd/systemd
000055790024d000       4 rw--- 0000000000182000 0fd:00000 /usr/lib/systemd/systemd
000055790046b000    1144 rw--- 0000000000000000 000:00000   [ anon ]
00007fd810000000     164 rw--- 0000000000000000 000:00000   [ anon ]
00007fd810029000   65372 ----- 0000000000000000 000:00000   [ anon ]
00007fd818000000     164 rw--- 0000000000000000 000:00000   [ anon ]
00007fd818029000   65372 ----- 0000000000000000 000:00000   [ anon ]
// 中间省略一堆输出
00007fd821c9f000       4 rw--- 0000000000000000 000:00000   [ anon ]
00007fffaf7c0000     132 rw--- 0000000000000000 000:00000   [ stack ]
00007fffaf7e5000       8 r-x-- 0000000000000000 000:00000   [ anon ]
ffffffffff600000       4 r-x-- 0000000000000000 000:00000   [ anon ]
mapped: 191168K    writeable/private: 18216K    shared: 0K
```

参数：
- d: (device) 显示设备名
- p: (path) 显示完整的文件路径

pmap命令的输出：
- Mapping:  file backing the map , or '[ anon ]' for allocated memory, or '[ stack ]' for the program stack. 
- Offset:  offset into the file 
- Device:  device name (major:minor)  

第一行是进程的启动参数。
最后一行是进程的内存统计，其中:
- mapped: 该进程映射的虚拟地址空间大小，对应top的VIRT、ps的VSZ
- writeable/private: 表示进程所占用的私有地址空间大小，也就是该进程实际使用的内存大小     
- shared: 和其他进程共享的内存大小

# /proc/pid/maps

`/proc/pid/maps`可以看到简单的进程内存区域使用状态。

```sh
[root@host143 ~]# cat /proc/1/maps
5578ffecb000-55790002b000 r-xp 00000000 fd:00 17643364                   /usr/lib/systemd/systemd
55790022a000-55790024d000 r--p 0015f000 fd:00 17643364                   /usr/lib/systemd/systemd
55790024d000-55790024e000 rw-p 00182000 fd:00 17643364                   /usr/lib/systemd/systemd
55790046b000-557900589000 rw-p 00000000 00:00 0                          [heap]
7fd810000000-7fd810029000 rw-p 00000000 00:00 0 
# 省略一堆输出
```

maps的输出和内核每进程的vm_area_struct有对应关系。
第一列是虚拟内存地址的开始和结束。对应vm_start和vm_end。

第二列是这段内存的访问权限。对应vm_flags。
r表示可读，w表示可写，x表示可执行，p和s共用一个字段，互斥关系，p表示私有段，s表示共享段，如果没有相应权限，则用`-`代替。

第三列是偏移地址。对应vm_pgoff。
对file-back映射，表示此段虚拟内存起始地址在文件中以页为单位的偏移。对匿名映射，它等于0或者vm_start/PAGE_SIZE。

第四列是映射文件所属设备号。对匿名映射来说，因为没有文件在磁盘上，所以没有设备号，始终为00:00。对有名映射来说，是映射的文件所在设备的设备号.

第五列是inode节点。

第六列是映射文件。
对file-back来说，是映射的文件名。对匿名映射来说，是此段虚拟内存在进程中的角色。`[stack]`表示在进程中作为栈使用，`[heap]`表示堆。其余情况则无显示。



# /proc/pid/smaps

smaps能够看到看到每个进程内存区域的使用详情。
```sh
[root@host143 ~]# cat /proc/1/smaps
5578ffecb000-55790002b000 r-xp 00000000 fd:00 17643364                   /usr/lib/systemd/systemd
Size:               1408 kB  # 虚拟内存大小
Rss:                1156 kB
Pss:                1156 kB
Shared_Clean:          0 kB
Shared_Dirty:          0 kB
Private_Clean:      1156 kB
Private_Dirty:         0 kB
Referenced:         1156 kB
Anonymous:             0 kB
AnonHugePages:         0 kB
Swap:                  0 kB
KernelPageSize:        4 kB
MMUPageSize:           4 kB
Locked:                0 kB
VmFlags: rd ex mr mw me dw sd 
# 以下省略
```

VmFlags含义：
```
rd  - readable
wr  - writeable
ex  - executable
sh  - shared
mr  - may read
mw  - may write
me  - may execute
ms  - may share
gd  - stack segment growns down
pf  - pure PFN range
dw  - disabled write to the mapped file
lo  - pages are locked in memory
io  - memory mapped I/O area
sr  - sequential read advise provided
rr  - random read advise provided
dc  - do not copy area on fork
de  - do not expand area on remapping
ac  - area is accountable
nr  - swap space is not reserved for the area
ht  - area uses huge tlb pages
ar  - architecture specific flag
dd  - do not include area into core dump
sd  - soft-dirty flag
mm  - mixed map area
hg  - huge page advise flag
nh  - no-huge page advise flag
mg  - mergable advise flag
```


# /proc/pid/status

status可以看到进程状态概览，包括内存部分。
```sh
[root@host143 ~]# cat /proc/1/status
Name:	systemd
Umask:	0000
State:	S (sleeping)
Tgid:	1
Ngid:	0
Pid:	1
PPid:	0
TracerPid:	0
Uid:	0	0	0	0
Gid:	0	0	0	0
FDSize:	256
Groups:	
VmPeak:	  256700 kB
# 虚拟内存大小，对应top的VIRT，ps的VSZ
VmSize:	  191164 kB
# 进程锁住的物理内存大小，锁住的物理内存无法交换到硬盘
# 和mlock()调用有关
VmLck:	       0 kB
VmPin:	       0 kB
VmHWM:	    4204 kB
# 使用的物理内存
VmRSS:	    4204 kB
# 匿名内存使用的物理内存
RssAnon:	    1620 kB
# file-back映射使用的物理内存
RssFile:	    2584 kB
# 共享区域使用的物理内存
RssShmem:	       0 kB
# 数据段的虚拟内存
VmData:	  148760 kB
# 用户态栈的虚拟内存
VmStk:	     132 kB
# 代码段的虚拟内存
VmExe:	    1408 kB
# 进程使用的库映射到虚拟内存空间的大小
VmLib:	    3728 kB
# 进程页表大小
VmPTE:	     120 kB
# 交换区的虚拟内存
VmSwap:	       0 kB
# 以下省略
```

# /proc/pid/statm

statm的输出好简洁，单位是page。
```
[root@host143 ~]# cat /proc/1/statm
47791 1051 646 352 0 37223 0
```
每列的含义如下：
```
size       (1) total program size
           (same as VmSize in /proc/[pid]/status)
resident   (2) resident set size
           (same as VmRSS in /proc/[pid]/status)
share      (3) shared pages (i.e., backed by a file)
text       (4) text (code)
lib        (5) library (unused in Linux 2.6)
data       (6) data + stack
dt         (7) dirty pages (unused in Linux 2.6)
```

# 参考

- [Linux内存管理 —— 文件系统缓存和匿名页的交换](https://blog.csdn.net/jasonchen_gbd/article/details/79462014)
- [proc(5) - Linux man page](https://linux.die.net/man/5/proc)
- [linux proc maps文件分析](https://blog.csdn.net/lijzheng/article/details/23618365)
