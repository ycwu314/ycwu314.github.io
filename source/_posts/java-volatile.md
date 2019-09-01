---
title: java volatile
date: 2019-08-16 18:00:44
tags: [Java, 多线程, 高并发]
categories: [java]
keywords: [volatile 线程安全, happens before volatile, volatile 场景, volatile 内存屏障]
description: volatile解决多线程对共享变量可见性的问题。volatile最合适的场景是简单状态变量的发布。
---

上次简单讲了Java内存模型，有了铺垫，这次可以聊聊volatile关键字。
- {% post_link jmm-java-memory-model %}

# 线程安全问题

## 原子性

多个操作，要么全部执行，要么都不执行。
数据库事务的原子性很常见。多线程操作也有原子性的要求。

## 可见性

一个线程修改了共享变量，结果能够立即被其他线程看到。
回忆java内存模型文章，现代多核cpu，每个核心有独立的寄存器、缓存，并且共享内存。当一个线程修改了缓存、但结果没有回写到内存，就有可能导致另一个核心上线程使用了该核心上旧缓存数据，需要一个机制通知数据更新。

## 有序性

编译器、cpu能够对代码重排序，提高执行性能。
如果不做限制多线程的重排序，就有可能导致错误的执行结果。JMM定义了**as-if-serial语义**，对重排序做了约束。

# volatile和使用场景

happens-before规则有一条：
>volatile变量规则：被volatile修饰的变量，写操作happens-before后续的读操作

volatile保证共享变量的可见性。被volatile修饰的变量，不会写入到cpu cache，只会存储在内存，每次访问该变量，都直接从内存读取，**解决多线程对共享变量可见性的问题**。

因为volatile只提供可见性支持，使用volatile的前提是：
- 对变量的写操作不依赖于当前值
- 该变量没有包含在具有其他变量的不变式中

volatile最适合应用在简单的标记。
```java
private volatile boolean hasInit = false;
public void init(){
    if(!hasInit){
        hasInit = true;
        // do sth else
    }
}
```
`hasInit`变量的写操作不依赖于当前hashInit的值。


# volatile底层实现

cpu指令中，有load、store指令。
- load：将内存数据复制到cpu的缓存。
- store：将cpu缓存的数据刷新到内存中。

有专门的load store unit，负责load/store指令的处理。
{% asset_img v1_load_store_unit.png "load store unit" %}

在此基础上，有2种内存屏障：Load Barrier和Store Barrier。内存屏障的作用
- 禁止内存屏障两侧的指令重排序
- 强制把写缓冲区的脏数据写回主内存(dirty cache pages write back to memory)，使得其他核心对应的缓存行失效

根据load、store操作组合的不同，java有4种内存屏障。
1. LoadLoad：该屏障确保Load1数据的装载先于Load2及其后所有装载指令的的操作
```
Load1;
LoadLoad;
Load2
```

2. StoreStore：该屏障确保Store1立刻刷新数据到内存(使其对其他处理器可见)的操作先于Store2及其后所有存储指令的操作
```
Store1;
StoreStore;
Store2
```

3. LoadStore：确保Load1的数据装载先于Store2及其后所有的存储指令刷新数据到内存的操作
```
Load1;
LoadStore;
Store2	
```

4. StoreLoad：该屏障确保Store1立刻刷新数据到内存的操作先于Load2及其后所有装载装载指令的操作。它会使该屏障之前的所有内存访问指令(存储指令和访问指令)完成之后,才执行该屏障之后的内存访问指令
```
Store1;
StoreLoad;
Load2
```

StoreLoad是最强的屏障语义，开销也是最大。不同架构的cpu，一般都会支持StoreLoad。
**volatile在变量读、写之前分别插入内存屏障，禁止重排序**。普通变量、volatile变量的操作顺序和插入内存屏障关系如下
{% asset_img v1_volatile-load-store.png "volatile load store" %}
（图片来源：`https://stackoverflow.com/questions/51700223/a-puzzle-on-how-java-implement-volatile-in-new-memory-model-jsr-133`）

# volatile和synchronized

完整的线程安全，要包括原子性、可见性、有序性。volatile只解决了可见性。需要完整线程安全的场景，应该用synchronized。
volatile底层指令实现比synchronized简单。但是由于不使用cpu缓存，变量的访问要慢一些。

# 小结

volatile解决多线程对共享变量**可见性**的问题。
volatile不能替代synchronized实现锁的能力。

# 参考

- [正确使用 Volatile 变量](https://www.ibm.com/developerworks/cn/java/j-jtp06197.html)
- [一文解决内存屏障](https://monkeysayhi.github.io/2017/12/28/%E4%B8%80%E6%96%87%E8%A7%A3%E5%86%B3%E5%86%85%E5%AD%98%E5%B1%8F%E9%9A%9C/)
