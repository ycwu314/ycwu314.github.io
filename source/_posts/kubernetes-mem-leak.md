---
title: kubernetes内存泄漏文章分享
date: 2020-07-03 11:42:37
tags: [kubernetes, linux]
categories: [kubernetes]
keywords: [no space left on device, SLUB: Unable to allocate memory on node, memcg]
description: 在linux 3.10上遇到k8s内存泄漏问题，分享几篇相关的好文章。
---

# 背景

公司使用老版本的linux 3.10内核，使用kubernetes时不时遇到内存泄漏导致pod重启的问题。
于是查了资料，分享几篇文章和笔记，后续再深入研究。
<!-- more -->

强烈推荐：
- [为什么容器内存占用居高不下，频频 OOM](https://eddycjy.com/posts/why-container-memory-exceed/)
- [为什么容器内存占用居高不下，频频 OOM（续）](https://eddycjy.com/posts/why-container-memory-exceed2/)
- [how-much-is-too-much-the-linux-oomkiller-and-used-memory](https://medium.com/faun/how-much-is-too-much-the-linux-oomkiller-and-used-memory-d32186f29c9d)
- [a-deep-dive-into-kubernetes-metrics-part-3-container-resource-metrics](https://blog.freshtracks.io/a-deep-dive-into-kubernetes-metrics-part-3-container-resource-metrics-361c5ee46e66)
- [Linux Cgroup系列（04）：限制cgroup的内存使用（subsystem之memory）](https://segmentfault.com/a/1190000008125359)
- [cgroup 泄露](https://www.bookstack.cn/read/kubernetes-practice-guide/troubleshooting-summary-cgroup-leaking.md)
- [诊断修复 TiDB Operator 在 K8s 测试中遇到的 Linux 内核问题](https://zhuanlan.zhihu.com/p/66895097)
- [Cgroup泄漏--潜藏在你的集群中](https://tencentcloudcontainerteam.github.io/2018/12/29/cgroup-leaking/)

# kmem泄漏现象

当k8s发生内存泄漏，dmesg有一些特征：
```sh
[root@master-29 ~]# dmesg -T | grep SLUB | head
[五 7月  3 00:00:50 2020] SLUB: Unable to allocate memory on node -1 (gfp=0x80d0)
[五 7月  3 00:00:50 2020] SLUB: Unable to allocate memory on node -1 (gfp=0x80d0)
```

```sh
[root@master-29 ~]# dmesg -T | grep kmem
[五 7月  3 00:05:56 2020] kmem: usage 3868836kB, limit 9007199254740988kB, failcnt 0
[五 7月  3 00:11:10 2020] kmem: usage 3871544kB, limit 9007199254740988kB, failcnt 0
```

```sh
[root@master-29 ~]# dmesg -T | grep 'Memory cgroup' | head
[五 7月  3 00:05:57 2020] Memory cgroup stats for /kubepods/burstable/pod20edac81-191c-4bc6-b85f-e23a65bc7931: cache:0KB rss:0KB rss_huge:0KB mapped_file:0KB swap:0KB inactive_anon:0KB active_anon:0KB inactive_file:0KB active_file:0KB unevictable:0KB
[五 7月  3 00:05:57 2020] Memory cgroup stats for /kubepods/burstable/pod20edac81-191c-4bc6-b85f-e23a65bc7931/47fe2a20f8dabf213dbcd0995ab220c7df41eea7e5ac2f444e2d9dab2a49ed39: cache:0KB rss:44KB rss_huge:0KB mapped_file:0KB swap:0KB inactive_anon:0KB active_anon:44KB inactive_file:0KB active_file:0KB unevictable:0KB
[五 7月  3 00:05:57 2020] Memory cgroup stats for /kubepods/burstable/pod20edac81-191c-4bc6-b85f-e23a65bc7931/26879c55393e26dbccdf7dfba2fcba9d5be00cd92f1be6929c24d9725a2adcdf: cache:40KB rss:325384KB rss_huge:202752KB mapped_file:0KB swap:0KB inactive_anon:0KB active_anon:325276KB inactive_file:4KB active_file:0KB unevictable:0KB
[五 7月  3 00:05:57 2020] Memory cgroup out of memory: Kill process 789343 (java) score 1074 or sacrifice child
```

```sh
[root@master-29 ~]# dmesg -T | grep 'oom-killer' | head
[五 7月  3 00:05:56 2020] java invoked oom-killer: gfp_mask=0xd0, order=0, oom_score_adj=996
[五 7月  3 00:11:10 2020] java invoked oom-killer: gfp_mask=0xd0, order=0, oom_score_adj=996
[五 7月  3 00:16:19 2020] java invoked oom-killer: gfp_mask=0xd0, order=0, oom_score_adj=996
```

k8s会提示`no space left on device`(注意是`/sys/fs/cgroup/memory`)
```
Error response from daemon: oci runtime error: container_linux.go:247:
starting container process caused "process_linux.go:258: applying
cgroup configuration for process caused \"mkdir
/sys/fs/cgroup/memory/kubepods/burstable/podfxxxxx/xxxxxxx:
no space left on device
```

# kmem accounting

cgroup-v1的说明：[Memory Resource Controller](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v1/memory.html)
>With the Kernel memory extension, the Memory Controller is able to limit the amount of kernel memory used by the system. Kernel memory is fundamentally different than user memory, since it can’t be swapped out, which makes it possible to DoS the system by consuming too much of this precious resource.
>
>Kernel memory accounting is enabled for all memory cgroups by default. But it can be disabled system-wide by passing cgroup.memory=nokmem to the kernel at boot time. In this case, kernel memory will not be accounted at all.

要点：
- kernel内存不能被swap
- 默认对所有memory cgrop开启kmem accounting

引用煎鱼的博客:
>memcg 是 Linux 内核中管理 cgroup 内存的模块，但实际上在 Linux 3.10.x 的低内核版本中存在不少实现上的 BUG，其中最具代表性的是 memory cgroup 中 kmem accounting 相关的问题（在低版本中属于 alpha 特性）：
>- slab 泄露：具体可详见该文章 [SLUB: Unable to allocate memory on node -1](https://pingcap.com/blog/try-to-fix-two-linux-kernel-bugs-while-testing-tidb-operator-in-k8s/#bug-1-unstable-kmem-accounting) 中的介绍和说明。
>- memory cgroup 泄露：在删除容器后没有回收完全，而 Linux 内核对 memory cgroup 的总数限制是 65535 个，若频繁创建删除开启了 kmem 的 cgroup，就会导致无法再创建新的 memory cgroup。


低版本的3.10内核，一旦开启了kmem_limit就可能会导致不能彻底删除memcg和对应的cssid。
查看内核相关memcg配置：
```sh
# uname -r : 输出内核版本
[root@host143 ~]# cat /boot/config-`uname -r`|grep CONFIG_MEMCG
CONFIG_MEMCG=y
CONFIG_MEMCG_SWAP=y
CONFIG_MEMCG_SWAP_ENABLED=y
CONFIG_MEMCG_KMEM=y
```

kubelet 和 runc 都会给 memory cgroup 开启 kmem accounting，所以要规避这个问题，就要保证kubelet 和 runc 都关闭 kmem accounting。（但是不如直接升级内核利索）

解决方案有2个：
1. 关闭 kmem accounting：
```
cgroup.memory=nokmem
```
也可以通过 kubelet 的 nokmem Build Tags 来编译解决：
```
$ kubelet GOFLAGS="-tags=nokmem"
```
但需要注意，kubelet 版本需要在 v1.14 及以上。

2. 升级内核版本
升级 Linux 内核至 kernel-3.10.0-1075.el7 及以上就可以修复这个问题，详细可见 [slab leak causing a crash when using kmem control group](https://bugzilla.redhat.com/show_bug.cgi?id=1507149#c101)，其在发行版中 CentOS 7.8 已经发布。


# 扩展：container_memory_working_set_bytes 和 oom-killer

kubernetes有几个和内存相关的指标：
>container_memory_max_usage_bytes(最大可用内存) >
>container_memory_usage_bytes(已经申请的内存+工作集使用的内存) >
>container_memory_working_set_bytes(工作集内存) >
>container_memory_rss(常驻内存集)

container_memory_usage_bytes包含了cache，如filesystem cache，当存在mem pressure的时候能够被回收。
container_memory_working_set_bytes 更能体现出mem usage，oom killer也是根据container_memory_working_set_bytes 来决定是否oom kill的。


# slub内存泄漏debug

推荐大佬的几篇文章：
- [怎样诊断SLAB泄露问题](http://linuxperf.com/?p=148)
- [如何诊断SLUB问题](http://linuxperf.com/?p=184)
- [用KMEMLEAK检测内核内存泄漏](http://linuxperf.com/?p=188)

内存泄漏的种类：
>- 内存泄露（leak），alloc之后忘了free，导致内存占用不断增长；
>- 越界（overrun），访问了alloc分配的区域之外的内存，覆盖了不属于自己的数据；
>- 使用已经释放的内存（use after free），正常情况下，已经被free释放的内存是不应该再被读写的，否则就意味着程序有bug；
>- 使用未经初始化的数据（use uninitialised bytes），缺省模式下alloc分配的内存是不被初始化的，内存值是随机的，直接使用的话后果可能是灾难性的。

slub引入了red zone和poisoning机制，提供了更加方便的debug方式。

{% asset_img slub-object.png slub对象格式 %}

引用大佬的文章：
>Red zone来自于橄榄球术语，是指球场底线附近的区域，slub通过在每一个对象后面额外添加一块red zone区域来帮助检测越界(overrun)问题，在red zone里填充了特征字符，如果代码访问到了red zone就意味着越界了。
>Poisoning是通过往slub对象中填充特征字符的方式来检测use-after-free、use-uninitialised等问题，比如在分配slub对象时填充0x5a，在释放时填充0x6b，然后debug代码检查时如果看到本该是0x6b的位置变成了别的内容，就可能是发生了use-after-free，而本该是0x5a的位置如果变成了其它内容就意味着可能是use-uninitialised问题。

开启slub debug方式见：[如何诊断SLUB问题](http://linuxperf.com/?p=184)。

跟踪slub内核内存的另一个工具是kmemleak。
>kmemleak通过追踪kmalloc(), vmalloc(), kmem_cache_alloc()等函数，把分配内存的指针和大小、时间、stack trace等信息记录在一个rbtree中，等到调用free释放内存时就把相应的记录从rbtree中删除。

通过`/sys/kernel/debug/kmemleak`查看信息。
kmemleak的扫描算法存在误报的可能。

要启用kmemleak，前提是内核编译时在“Kernel hacking”中开启了 CONFIG_DEBUG_KMEMLEAK 选项。
```sh
[root@localhost bin]# cat /boot/config-`uname -r`  | grep -i kmem
CONFIG_MEMCG_KMEM=y
# CONFIG_DEVKMEM is not set
CONFIG_HAVE_DEBUG_KMEMLEAK=y
# CONFIG_DEBUG_KMEMLEAK is not set
CONFIG_HAVE_ARCH_KMEMCHECK=y
```

挂载以下文件系统：
```
# mount -t debugfs nodev /sys/kernel/debug/
```

默认每10分钟扫描内存一次，也可以手动触发
```
echo scan > /sys/kernel/debug/kmemleak
```