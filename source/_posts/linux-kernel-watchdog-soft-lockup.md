---
title: linux内核watchdog、NMI和soft lockup
date: 2020-07-15 21:04:24
tags: [linux]
categories: [linux]
keywords: [kernel watchdong, NMI, soft lockup, kernel panic]
description: 一些内核watchdog、NMI的资料整理。
---

之前在k8s内核内存泄漏，接触到kernel watchdog、soft lockup等概念，整理笔记。
相关文章：
- {% post_link kubernetes-mem-leak %}

<!-- more -->

# linux watchdog

watchdog是linux的一种监控机制，目的是监测系统运行的情况，一旦出现锁死，死机的情况，能及时重启机器（取决于设置策略），并收集crash dump。
在了解watchdog之前，先要了解NMI和lockup。

# NMI

ps. 此节内容摘抄自：[NMI是什么](http://linuxperf.com/?p=72)。

中断分为可屏蔽中断和非可屏蔽中断（NMI）。
NMI(non-maskable interrupt) ： 就是不可屏蔽的中断。
产生NMI的方式：
– NMI pin
– delivery mode NMI messages through system bus or local APIC serial bus

NMI通常用于通知操作系统发生了无法恢复的硬件错误。
- 无法恢复的硬件错误通常包括：芯片错误、内存ECC校验错、总线数据损坏等等。
- 当系统挂起，失去响应的时候，可以人工触发NMI，使系统重置，如果早已配置好了kdump，那么会保存crash dump以供分析。
- Linux还提供一种称为”NMI watchdog“的机制，用于检测系统是否失去响应（也称为lockup），可以配置为在发生lockup时自动触发panic。

中断是有优先级的：
>kernel线程 < 时钟中断 < NMI中断

其中，kernel 线程是可以被调度的，同时也是可以被中断随时打断的。


# lockup

ps. 此节内容摘抄自：[Linux Watchdog 机制](https://blog.csdn.net/ericstarmars/article/details/81750919)。

lockup，是指某段内核代码一直占用CPU资源、并且不释放。
>只有内核代码才能引起lockup，因为用户代码是可以被抢占的，不可能形成lockup。
>其次内核代码必须处于禁止内核抢占的状态(preemption disabled)，因为Linux是可抢占式的内核，只在某些特定的代码区才禁止抢占（例如spinlock），在这些代码区才有可能形成lockup。

Lockup分为两种：soft lockup 和 hard lockup。
soft lockup 则是单个CPU被一直占用的情况（中断仍然可以响应）。
hard lockup 发生在CPU屏蔽中断的情况下。



## soft lockup

SoftLockup 检测首先需要对每一个CPU core注册叫做watchdog的kernel线程。即`[watchdog/0]`，`[watchdog/1]`，etc.
```sh
[root@host143 ~]# ps aux | grep watchdog
root         11  0.0  0.0      0     0 ?        S    7月15   0:01 [watchdog/0]
root         12  0.0  0.0      0     0 ?        S    7月15   0:01 [watchdog/1]
root         17  0.0  0.0      0     0 ?        S    7月15   0:01 [watchdog/2]
root         22  0.0  0.0      0     0 ?        S    7月15   0:01 [watchdog/3]
```

同时，系统会有一个高精度的计时器hrtimer（一般来源于APIC），该计时器能定期产生时钟中断。
对应的中断处理例程是`kernel/watchdog.c: watchdog_timer_fn()`，在该例程中：
- 要递增计数器hrtimer_interrupts，这个计数器同时为hard lockup detector用于判断CPU是否响应中断；
- 还要唤醒`[watchdog/x]`内核线程，该线程的任务是更新一个时间戳；
- soft lock detector检查时间戳，如果超过soft lockup threshold一直未更新，说明`[watchdog/x]`未得到运行机会，意味着CPU被霸占，也就是发生了soft lockup。

注意，这里面的内核线程`[watchdog/x]`的目的是更新时间戳，该时间戳是被watch的对象。而真正的看门狗，则是由时钟中断触发的 watchdog_timer_fn()，这里面`[watchdog/x]`是被scheduler调用执行的，而watchdog_timer_fn()则是被中断触发的。

## hard lockup

>发生hard lockup的时候，CPU不仅无法执行其它进程，而且不再响应中断。
>检测hard lockup的原理利用了PMU的NMI perf event，因为NMI中断是不可屏蔽的，在CPU不再响应中断的情况下仍然可以得到执行，它再去检查时钟中断的计数器hrtimer_interrupts是否在保持递增，如果停滞就意味着时钟中断未得到响应，也就是发生了hard lockup

检测hard lockup的机制：NMI watchdog会利用到之前讲到的hrtimer。


# 修改watchdog

hard lockup检查机制依赖nmi_watchdog：
```
echo 1 > /proc/sys/kernel/nmi_watchdog
```

watchdog_thresh参数来定义发现softlockup以后系统panic的时间。
watchdog默认监控阈值是10s。
临时修改
```sh
sysctl -w kernel.watchdog_thresh=60
```
永久修改
```sh
echo 60 > /proc/sys/kernel/watchdog_thresh 
```

如果要在发生lockup的时候触发系统panic机制：
```
echo 1 > /proc/sys/kernel/softlockup_panic

echo 1 > /proc/sys/kernel/hardlockup_panic
```

# 扩展： 用户态watchdog

上面的lockup机制针对内核。事实上用户态watchdog可以监控用户程序，分为software watchdog和hardware watchdog。

software watchdog要安装软件包
```
yum install -y watchdog

systemctl start watchdog
```

hardware watchdog需要硬件支持。

# 扩展：linux panic 机制

Kernel panic是内核错误，是系统内核遇到无法处理的致命错误时才会产生的异常。对应windows的蓝屏。
当内核发生panic时，linux系统会默认立即重启系统，当然这只是默认情况，除非你修改了产生panic时重启定时时间，这个值默认情况下是0，即立刻重启系统。

# 参考

- [Linux Watchdog 机制](https://blog.csdn.net/ericstarmars/article/details/81750919)
- [Linux 内核中断内幕](https://www.ibm.com/developerworks/cn/linux/l-cn-linuxkernelint/index.html)
- [linux panic 机制](https://blog.csdn.net/dake_160413/article/details/64443274)


