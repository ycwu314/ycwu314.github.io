---
title: kubernetes swap memory
date: 2019-10-20 15:13:03
tags: [kubernetes]
categories: [kubernetes]
keywords: [kubernetes swap memory, kubernetes systemoom]
description: kubernetes不建议使用swap memory。k8s v1.8以后默认不支持swap，并且会启动报错。swap会使得内存限额和调度器变得复杂。
---

# 问题背景

之前发生过staragent异常，导致云效流水线部署失败：
- {% post_link aliyun-staragent-deploy-failure %}

回想起来，是在开启microk8s之后才发生的。于是怀疑是microk8s导致。
<!-- more -->
```bash
kubectl describe node izwz9h8m2chowowqckbcy0z
```
在Events看到几个SystemOOM警告。
```
Events:
  Type     Reason                   Age    From                                 Message
  ----     ------                   ----   ----                                 -------
  Normal   Starting                 5m57s  kube-proxy, izwz9h8m2chowowqckbcy0z  Starting kube-proxy.
  Normal   Starting                 5m46s  kubelet, izwz9h8m2chowowqckbcy0z     Starting kubelet.
  Warning  InvalidDiskCapacity      5m46s  kubelet, izwz9h8m2chowowqckbcy0z     invalid capacity 0 on image filesystem
  Warning  SystemOOM                5m46s  kubelet, izwz9h8m2chowowqckbcy0z     System OOM encountered, victim process: pip3, pid: 23143
  Warning  SystemOOM                5m46s  kubelet, izwz9h8m2chowowqckbcy0z     System OOM encountered, victim process: pip3, pid: 24161
  Warning  SystemOOM                5m46s  kubelet, izwz9h8m2chowowqckbcy0z     System OOM encountered, victim process: pip3, pid: 25349
```

从dmesg看，这个pip3进程申请了2G+的vm（what！！！）。
```
# dmesg | grep 23143
[1375956.718910] [23143]     0 23143   528095   435853  3997696    39263             0 pip3
[1375956.718916] Out of memory: Kill process 23143 (pip3) score 613 or sacrifice child
[1375956.719841] Killed process 23143 (pip3) total-vm:2112380kB, anon-rss:1743412kB, file-rss:0kB, shmem-rss:0kB
[1375957.190126] oom_reaper: reaped process 23143 (pip3), now anon-rss:0kB, file-rss:0kB, shmem-rss:0kB
```
不过很可惜，不是staragent相关进程。最初的假设不成立。
疑惑的是，swap内存空闲率很高。直接触发SystemOOM，太粗暴了。

```bash
# swapon
NAME          TYPE   SIZE  USED PRIO
/swapfile     file 947.2M 18.6M   -2
/swapfile.new file     2G   48K   -3
```

于是查阅一些资料，了解kubernetes对swap的使用情况。

# `--fail-swap-on`

默认情况下，系统开启swap会导致k8s启动失败。除非使用`--fail-swap-on`参数（[kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)）。
>--fail-swap-on
>Makes the Kubelet fail to start if swap is enabled on the node. (default true) (DEPRECATED: This parameter should be set via the config file specified by the Kubelet's --config flag. See https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/ for more information.)

如果为true（默认值）就要求必须要关闭swap，false是表示即使宿主开启了swap，kubelet也是可以成功启动，但是pod是允许使用swap了。

# 关于 swap memory 的讨论

2017年的这个issue讨论了swap问题：[Kubelet/Kubernetes should work with Swap Enabled #53533](https://github.com/kubernetes/kubernetes/issues/53533)。总结起来有这几点：

1. 开启swap，会使得内存限额和pod调度变得复杂。怎样衡量swap配置？调度器要怎样根据swap去调度？

>having swap available has very strange and bad interactions with memory limits. 
>For example, a container that hits its memory limit would then start spilling over into swap

2. kubernetes不是为了swap而设计。由于pod使用内存的复杂性，kubernetes缺少一个足够聪明的策略去协调不同pod对内存/swap的使用。k8s官方对此觉得产出投入比不高，不如把时间花在提高稳定性上。

>Support for swap is non-trivial. Guaranteed pods should never require swap. Burstable pods should have their requests met without requiring swap. BestEffort pods have no guarantee. The kubelet right now lacks the smarts to provide the right amount of predictable behavior here across pods.
>We discussed this topic at the resource mgmt face to face earlier this year. We are not super interested in tackling this in the near term relative to the gains it could realize. 

3. 在实际应用场景，如果不开启swap，应用就要为峰值内存申请内存资源，可能导致资源浪费。

>We have a cron job that occasionally runs into high memory usage (>30GB) and we don't want to permanently allocate 40+GB nodes.

4. v1.8后默认不用了swap。官方不推荐使用swap。开启swap后果自负，官方不背锅。

# 折中的做法

像批处理job这种容易产生高峰值内存的app，就要考虑开启swap。

