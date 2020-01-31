---
title:  wall time和monotonic time简介
date: 2020-01-28 23:26:09
tags: [linux, prometheus]
categories: [linux]
keywords: [wall time, monotonic time, jiffies, xtime]
description: linux的wall time 和 monotonic time简介。
---

# 背景

使用micrometer集成Prometheus的时候，发现对于时钟micrometer抽象了`wallTime`和`monotonicTime`，做下笔记。
<!-- more -->
micrometer的Clock接口如下。
```java
/**
 * Used to measure absolute and relative time.
 *
 * @see MockClock for a clock that can be manually advanced for use in tests.
 * @author Jon Schneider
 */
public interface Clock {
    Clock SYSTEM = new Clock() {
        @Override
        public long wallTime() {
            return System.currentTimeMillis();
        }

        @Override
        public long monotonicTime() {
            return System.nanoTime();
        }
    };

    /**
     * Current wall time in milliseconds since the epoch. Typically equivalent to
     * System.currentTimeMillis. Should not be used to determine durations. Used
     * for timestamping metrics being pushed to a monitoring system or for determination
     * of step boundaries (e.g. {@link StepLong}.
     *
     * @return Wall time in milliseconds
     */
    long wallTime();

    /**
     * Current time from a monotonic clock source. The value is only meaningful when compared with
     * another snapshot to determine the elapsed time for an operation. The difference between two
     * samples will have a unit of nanoseconds. The returned value is typically equivalent to
     * System.nanoTime.
     *
     * @return Monotonic time in nanoseconds
     */
    long monotonicTime();
}
```

# wall time

字面意义是墙上的时间，是真实时间。又叫real time。
对应java api：
```java
System.currentTimeMillis()
```

在linux内核中，使用xtime内存变量维护wall time。
wall time会收到系统时间调整的影响，例如ntp。

# monotonic time

monotonic，单调的。是系统启动以后流逝的时间（相对时间）。
对应Java api：
```java
System.nanoTime()
```
javadoc上的说明

>此方法只能用于测量已过的时间，与系统或钟表时间的其他任何时间概念无关。
>返回值表示从某一固定但任意的时间算起的毫微秒数（或许从以后算起，所以该值可能为负）。
>此方法提供毫微秒的精度，但不是必要的毫微秒的准确度。它对于值的更改频率没有作出保证。
>在取值范围大于约 292 年（263 毫微秒）的连续调用的不同点在于：由于数字溢出，将无法准确计算已过的时间。
>
>public static native long nanoTime();

由于可能存在数字溢出，比较两个nanoTime数值，应该使用相减的方式：
```java
long t0 = System.nanoTime();
long t1 = System.nanoTime();
// one should use {@code t1 - t0 < 0}, not {@code t1 < t0},
// because of the possibility of numerical overflow.
```

linux内核中，使用jiffies变量存储monotonic time。每次timer中断，jiffies增加一次。
>The original kernel timer system (called the "timer wheel) was based on incrementing a kernel-internal value (jiffies) every timer interrupt. 
>The timer interrupt becomes the default scheduling quantum, and all other timers are based on jiffies. 
>The timer interrupt rate (and jiffy increment rate) is defined by a compile-time constant called HZ. 

ps.
```
jiffy
英 ['dʒɪfi] 　 　 美 ['dʒɪfi] 　 　
n. 瞬间；一会儿
```

系统休眠时，monotonic time不会递增。
在linux中，还有raw monotonic time，不受ntp调节影响。
另外还有boot time，会累加上系统休眠的时间，它代表着系统上电后的总时间。


# 参考

- [Kernel Timer Systems](https://elinux.org/Kernel_Timer_Systems)
- [Linux时间子系统之三：时间的维护者：timekeeper](http://abcdxyzk.github.io/blog/2017/07/23/kernel-clock-3/)