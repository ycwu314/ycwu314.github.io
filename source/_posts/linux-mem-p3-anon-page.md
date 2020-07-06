---
title: linux内存系列3：匿名页
date: 2020-07-06 19:35:22
tags: [linux]
categories: [linux]
keywords: [anon page, pmap]
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


# 参考

- [Linux内存管理 —— 文件系统缓存和匿名页的交换](https://blog.csdn.net/jasonchen_gbd/article/details/79462014)