---
title: java volatile
date: 2019-08-16 18:00:44
tags: [Java, 多线程, 高并发]
categories: [java]
keywords: [volatile 线程安全, happens before volatile, volatile 场景]
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


# volatile和synchronized

完整的线程安全，要包括原子性、可见性、有序性。volatile只解决了可见性。需要完整线程安全的场景，应该用synchronized。
volatile底层指令实现比synchronized简单。但是由于不使用cpu缓存，变量的访问要慢一些。

# 小结

volatile解决多线程对共享变量**可见性**的问题。

# 参考

- [正确使用 Volatile 变量](https://www.ibm.com/developerworks/cn/java/j-jtp06197.html)

