---
title: java支持docker的资源限制
date: 2020-01-18 16:47:05
tags: [java, docker, linux, jvm]
categories: [java]
keywords: [java cgroups]
description: java 8u131 以后版本支持linux cgroups做资源限制。
---

# 背景

前2天开发环境挂了，原因是物理机部署了kafka进程，没有做资源限制，耗光cpu资源：
{% asset_img java-app-resources-no-limit.png java-app-resources-no-limit %}

<!-- more -->

cgroups是linux的资源隔离方式，是docker的基础技术，可以限制cpu、内存资源的使用。
后来和运维同事聊了，应该使用cgroups限制资源，但是部署的java版本太老（java 8 u60），不支持。

# 限制jvm使用内存

jvm中使用`-Xmx`限制jvm最大内存使用。
在docker里，使用`-m`参数指定容器的内存限制。
```
docker run -m 1G -it openjdk:8u60
```
如果使用旧版本jvm，那么进入容器，发现（在一台32G的服务器上）
```
[root@bdgpu bin]# docker exec -it 8e9d40b2878d  bash
bash-4.4# java -XX:+PrintFlagsFinal -version | grep MaxHeapSize
    uintx MaxHeapSize                              := 32210157568                         {product}
```
在java 8u131之前，docker中的jvm检测到的是宿主机的内存信息，它无法感知容器的资源上限，这样可能会导致意外的情况。

java 8u131+ 可以通过开启实验性参数来实现cgroups限制：
- `-XX:+UnlockExperimentalVMOptions`
- `-XX:+UseCGroupMemoryLimitForHeap`。

java11废弃了`UseCGroupMemoryLimitForHeap`，使用`UseContainerSupport`代替：
- [Remove deprecated experimental flag UseCGroupMemoryLimitForHeap](http://hg.openjdk.java.net/jdk/jdk/rev/48b6b247eb7a)

# UseContainerSupport

java 8u191 新增`-XX:+UseContainerSupport`参数，且默认开启：[JDK 8u191 Update Release Notes](https://www.oracle.com/technetwork/java/javase/8u191-relnotes-5032181.html)。
该参数只在linux系统生效（因为是依赖cgroups嘛）。

提供了3个新的内存参数，微调docker中jvm内存使用：
- `-XX:InitialRAMPercentage`
- `-XX:MaxRAMPercentage`
- `-XX:MinRAMPercentage`

同时干掉
>These options replace the deprecated Fraction forms (-XX:InitialRAMFraction, -XX:MaxRAMFraction, and -XX:MinRAMFraction).

具体效果参见：[-XX:[+|-]UseContainerSupport](https://www.eclipse.org/openj9/docs/xxusecontainersupport/)，这里复制默认的内存限制。

| Container memory limit <size> | Maximum Java heap size | Container memory limit <size> | Maximum Java heap size |
| ----------------------------- | ---------------------- | ----------------------------- | ---------------------- |
| Less than 1 GB                | 50% <size>             | Less than 1 GB                | 50% <size>             |
| 1 GB - 2 GB                   | <size> - 512 MB        | 1 GB - 2 GB                   | <size> - 512 MB        |
| Greater than 2 GB             | 75% <size>             | Greater than 2 GB             | 75% <size>             |

# 限制jvm使用cpu资源

java 8u191 增加了`-XX:ActiveProcessorCount=count`，可以用来指定cpu的个数，覆盖原来jvm自动检测cpu个数。

这个bug记录讨论了相关问题：[JDK-8189497 : Improve docker container detection and resource configuration usage](https://bugs.java.com/bugdatabase/view_bug.do?bug_id=8189497)。

对应一个[CR](http://cr.openjdk.java.net/~bobv/8146115/webrev.03/)，其中`osContainer_linux.cpp`是重点。
去openjdk搜索了此时最新源码：http://hg.openjdk.java.net/jdk/jdk/rev/931354c6323d
```cpp
bool  OSContainer::_is_initialized   = false;
bool  OSContainer::_is_containerized = false;
CgroupSubsystem* cgroup_subsystem;

// more code

int OSContainer::active_processor_count() {
  assert(cgroup_subsystem != NULL, "cgroup subsystem not available");
  return cgroup_subsystem->active_processor_count();
}

```
由cgroup_subsystem提供实现。

`active_processor_count`实现见[cgroupSubsystem_linux.cpp](http://hg.openjdk.java.net/jdk/jdk/file/931354c6323d/src/hotspot/os/linux/cgroupSubsystem_linux.cpp)。
支持cpuset和cpushare。
```cpp
/* active_processor_count
 *
 * Calculate an appropriate number of active processors for the
 * VM to use based on these three inputs.
 *
 * cpu affinity
 * cgroup cpu quota & cpu period
 * cgroup cpu shares
 *
 * Algorithm:
 *
 * Determine the number of available CPUs from sched_getaffinity
 *
 * If user specified a quota (quota != -1), calculate the number of
 * required CPUs by dividing quota by period.
 *
 * If shares are in effect (shares != -1), calculate the number
 * of CPUs required for the shares by dividing the share value
 * by PER_CPU_SHARES.
 *
 * All results of division are rounded up to the next whole number.
 *
 * If neither shares or quotas have been specified, return the
 * number of active processors in the system.
 *
 * If both shares and quotas have been specified, the results are
 * based on the flag PreferContainerQuotaForCPUCount.  If true,
 * return the quota value.  If false return the smallest value
 * between shares or quotas.
 *
 * If shares and/or quotas have been specified, the resulting number
 * returned will never exceed the number of active processors.
 *
 * return:
 *    number of CPUs
 */
int CgroupSubsystem::active_processor_count() {
  int quota_count = 0, share_count = 0;
  int cpu_count, limit_count;
  int result;

  // We use a cache with a timeout to avoid performing expensive
  // computations in the event this function is called frequently.
  // [See 8227006].
  CachingCgroupController* contrl = cpu_controller();
  CachedMetric* cpu_limit = contrl->metrics_cache();
  if (!cpu_limit->should_check_metric()) {
    int val = (int)cpu_limit->value();
    log_trace(os, container)("CgroupSubsystem::active_processor_count (cached): %d", val);
    return val;
  }

  cpu_count = limit_count = os::Linux::active_processor_count();
  int quota  = cpu_quota();
  int period = cpu_period();
  int share  = cpu_shares();

  if (quota > -1 && period > 0) {
    quota_count = ceilf((float)quota / (float)period);
    log_trace(os, container)("CPU Quota count based on quota/period: %d", quota_count);
  }
  if (share > -1) {
    share_count = ceilf((float)share / (float)PER_CPU_SHARES);
    log_trace(os, container)("CPU Share count based on shares: %d", share_count);
  }

  // If both shares and quotas are setup results depend
  // on flag PreferContainerQuotaForCPUCount.
  // If true, limit CPU count to quota
  // If false, use minimum of shares and quotas
  if (quota_count !=0 && share_count != 0) {
    if (PreferContainerQuotaForCPUCount) {
      limit_count = quota_count;
    } else {
      limit_count = MIN2(quota_count, share_count);
    }
  } else if (quota_count != 0) {
    limit_count = quota_count;
  } else if (share_count != 0) {
    limit_count = share_count;
  }

  result = MIN2(cpu_count, limit_count);
  log_trace(os, container)("OSContainer::active_processor_count: %d", result);

  // Update cached metric to avoid re-reading container settings too often
  cpu_limit->set_value(result, OSCONTAINER_CACHE_TIMEOUT);

  return result;
}
```

# 小结

docker里的应用应该使用java 8u191 以后jvm版本，支持容器memory和cpu限制。
