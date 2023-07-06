---
title: 低版本jdk不能正常识别pod内存限制的case
date: 2020-04-13 17:48:22
tags: [kubernetes, java]
categories:  [kubernetes]
keywords: [java cgroups]
description: 低版本Java 8 不支持cgroups，导致内存计算使用了物理机内存大小。
---

# 背景

把cas server 4.x （运行在tomcat中）塞到k8s运行，经常被吐槽消耗大量内存。
<!-- more -->
{% asset_img kubectl-top kubectl-top %}

# 排查过程

```
kubectl exec -it -n prophet cas-tomcat-deployment-xxx-xxx bash
```

启动jmap失败，根本没有jmap命令😥。问了容器组，当时为了精简镜像，把jdk工具都干掉了。。。r u kidding me。。。
于是从物理机kubectl cp一份jdk 1.8.0_242进去（注意版本）。
```
bash-4.3# ./jmap 8
Attaching to process ID 8, please wait...
Error attaching to process: sun.jvm.hotspot.runtime.VMVersionMismatchException: Supported versions are 25.242-b08. Target VM is 25.60-b23
sun.jvm.hotspot.debugger.DebuggerException: sun.jvm.hotspot.runtime.VMVersionMismatchException: Supported versions are 25.242-b08. Target VM is 25.60-b23
```
这里有2个要点：
- jdk instrument工具有版本兼容性，包括minor版本（以前很少留意这一点）
- 容器使用的java版本是1.8.0_60 （划重点）

于是又从物理机cp一份jdk 1.8.0_60到容器。

了解到tomcat启动时候并没有设置jvm内存参数(`catalina.sh`)。使用`jinfo`看下默认jvm申请内存大小
```
VM Flags:
Non-default VM flags: -XX:CICompilerCount=15 -XX:InitialHeapSize=2147483648 -XX:MaxHeapSize=32210157568 -XX:MaxNewSize=10736369664 -XX:MinHeapDeltaBytes=524288 -XX:NewSize=715653120 -XX:OldSize=1431830528 -XX:+UseCompressedClassPointers -XX:+UseCompressedOops -XX:+UseFastUnorderedTimeStamps -XX:+UseParallelGC 
```
初始化heap就申请了2G，最大heap是32G，肯定有问题。

（期间容器又被重启过）gc之前（使用`jmap -heap <pid>`）
```
Heap Usage:
PS Young Generation
Eden Space:
   capacity = 6462373888 (6163.0MB)
   used     = 1415239592 (1349.6776504516602MB)
   free     = 5047134296 (4813.32234954834MB)
   21.89968603685965% used
From Space:
   capacity = 71303168 (68.0MB)
   used     = 0 (0.0MB)
   free     = 71303168 (68.0MB)
   0.0% used
To Space:
   capacity = 99614720 (95.0MB)
   used     = 0 (0.0MB)
   free     = 99614720 (95.0MB)
   0.0% used
PS Old Generation
   capacity = 1700265984 (1621.5MB)
   used     = 118246632 (112.7687759399414MB)
   free     = 1582019352 (1508.7312240600586MB)
   6.954596111004712% used

```

gc之后(通过`jmap -histo:live`触发)：
```
Heap Usage:
PS Young Generation
Eden Space:
   capacity = 7146569728 (6815.5MB)
   used     = 75274344 (71.7872085571289MB)
   free     = 7071295384 (6743.712791442871MB)
   1.0532933542238854% used
From Space:
   capacity = 2097152 (2.0MB)
   used     = 0 (0.0MB)
   free     = 2097152 (2.0MB)
   0.0% used
To Space:
   capacity = 102760448 (98.0MB)
   used     = 0 (0.0MB)
   free     = 102760448 (98.0MB)
   0.0% used
PS Old Generation
   capacity = 2156396544 (2056.5MB)
   used     = 82477096 (78.65628814697266MB)
   free     = 2073919448 (1977.8437118530273MB)
   3.8247648017005913% used
```
其实内存使用率相当的低。

ps. 想研究heap内容，可以这么dump，再从容器中拷贝到物理机。
```
jmap -dump:live,format=b,file=cas_mem_8G.dump
```

# k8s resources配置

再看下对应deployment中的资源设置。
```yml
resources:
  limits:
    cpu: 1000m
    memory: 10000Mi
  requests:
    cpu: 10m
    memory: 100Mi
```

>Requests: 容器使用的最小资源需求，作为容器调度时资源分配的判断依赖。只有当节点上可分配资源量>=容器资源请求数时才允许将容器调度到该节点。但Request参数不限制容器的最大可使用资源。
>Limits: 容器能使用资源的资源的最大值，设置为0表示使用资源无上限。
>Request能够保证Pod有足够的资源来运行，而Limit则是防止某个Pod无限制地使用资源，导致其他Pod崩溃。两者之间必须满足关系: 0<=Request<=Limit<=Infinity (如果Limit为0表示不对资源进行限制，这时可以小于Request)

显然，pod中的java并没有正确识别`resources.limits.memory`，直接读取了物理机的内存大小。

# 问题回顾

前面的整理步骤有点凌乱。
- k8s deployment的资源限制不合理
- java启动命令行没有做内存限制，并且java版本过低，对于cgroups隔离支持有问题。导致直接使用整个物理机内存作为计算申请内存的基础（应该使用cgroups限制的内存作为计算依据）。

之前整理过资料，但是都忘记了：
- [java-8-support-cgroups-docker-limit](/posts/java-8-support-cgroups-docker-limit)

# 解决

- 重新设置k8s yaml的resources limits，改为2G。
- 原来java底包是jdk_1.8.0_60，不能正确识别cgroups配置。现在升级为jdk_1.8.0_221。
- 增加xmx配置。因为默认使用1/4可见内存。
- 检查其他容器是否有相同类型问题。
 
