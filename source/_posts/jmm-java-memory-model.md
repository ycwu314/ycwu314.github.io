---
title: 聊聊java内存模型
date: 2019-08-16 14:44:24
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [java内存模型, jmm, happens-before, as-if-serial]
description: java内存模型规范了JVM和内存交互行为，解决多线程对共享变量的访问和修改的安全性，以及约束指令重排序；主要包括happens-before规则和as-if-serial语义。
---

# 硬件架构

{% asset_img v1_java-memory-model-pc.png "java memory model" %}

存储器的速度：缓存>内存。
容量：缓存<内存。
价格：缓存>内存。

现实情况是在速度、容量、价格之间平衡。
cpu要读取数据，数据会经过内存、缓存。如果发生修改，则更新路径缓存、内存。

从图上可见，读取、修改数据，要经历多级存储器，如果多线程操作，就有可能产生数据不一致，需要有机制处理线程安全。

# java内存结构

最简化的java内存结构，是分为堆内存（heap）和栈内存（stack）。
{% asset_img v1_java-memory-model-1.png "java memory model"  %}
stack是每个线程独占内存，用于存放本地变量和引用。heap是各个线程共享的内存，创建对象将存放在这个区域。下面这张图更为细致的展现了java内存结构

{% asset_img v1_java-memory-model-3.png "java memory model" %}
**Local variable**是本地变量，可以是原始类型( boolean, byte, short, char, int, long, float, double)，也可以是指向堆中对象的引用。

# java内存模型和硬件架构的鸿沟

硬件架构不会区分java的stack和heap。Java内存模型中stack、heap数据也可能出现在硬件的寄存器、缓存、内存。
{% asset_img v1_java-memory-model-gap.png "java memory model" %}
数据跨越多个区域存储，就有可能产生问题：
- 共享变量被多个线程修改后的可见性
- 读、检查和写共享变量的竞争条件

## 可见性

考虑这样的情况，2个线程运行在2个cpu核心上，一开始都读取了`obj.count`，并且缓存到各自的cpu的cache。那么其中一个cpu修改了缓存中`obj.count`的值，在没有回写到内存之前，另一个cpu缓存中`obj.count`的值依然是旧的。
{% asset_img v1_java-memory-model-visibility.png "java memory model" %}
Java解决可见性问题，使用`volatile`关键字。

## 竞争条件

多个线程对共享变量修改，会出现竞争条件(race condition)。
>竞争条件指多个线程或者进程在读写一个共享数据时结果依赖于它们执行的相对时间的情形。

2个线程同时对`obj.count`进行加1操作。线程A在缓存中更新了`obj.count`，此时还没有回写到内存，如果这时候线程B也进行加1操作，它不知道`obj.count`已经发生变化。导致2个线程操作的最终结果是2，并非期望的3。
{% asset_img java-memory-model-race-condition.png "race condition" %}
Java解决竞争条件，是对共享变量的读写操作使用同步或者锁的机制，即synchronized或者各种Lock的变种。

## 重排序

为了优化代码执行，计算机实际执行指令的顺序，可能和源码中指令顺序不一致。
```
x=1
y=2
z=3
x=x+1
```
一个可能的执行顺序是
```
x=1
z=3
y=2
x=x+1
```
重排序可能发生在编译阶段、处理器执行阶段。
Java使用了**as-if-serial语义**，限制某些场景的重排序。

# happens-before 和 as-if-serial语义

因为jvm内存结构和硬件架构不一致，会产生并发线程对共享变量的可见性和竞争条件问题，所以JVM规范描述了java内存模型，解决多线程对共享变量的读取、修改问题。
JMM定义了**happens-before**规则，保证一个线程的操作对另一个线程是可见的（Happens-before relationship is a guarantee that action performed by one thread is visible to another action in different thread.）。

happens-before有多条规则，核心的有：
- 单个线程规则：单个线程内按照代码顺序，写在前面的happens-before后面的
- 监视器锁规则：unlock监视器锁的操作，happens-before后续的获取监视器操作
- volatile变量规则：被volatile修饰的变量，写操作happens-before后续的读操作
- 传递性：A happens-before B，B happens-before C，那么A happens-before C

对于重排序的问题，JMM提出了**as-if-serial语义**：不管怎么重排序，单线程下的执行结果不能被改变。

# 参考

- [Java Memory Model](http://tutorials.jenkov.com/java-concurrency/java-memory-model.html)
- [JSR-133 Java Memory Model and Thread Specification 1.0 Proposed Final Draft](https://download.oracle.com/otndocs/jcp/memory_model-1.0-pfd-spec-oth-JSpec/)
- [Java - Understanding Happens-before relationship](https://www.logicbig.com/tutorials/core-java-tutorial/java-multi-threading/happens-before.html)



	
