---
title: Java LongAdder 原理
date: 2019-08-25 20:00:00
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [longadder 原理, longadder striped64, longadder vs atomiclong]
description: LongAdder继承了Striped64，是高效的计数器。
---

有了Striped64的基础，LongAdder就见多了。
相关文章：
- {% post_link java-striped64 %}

{% asset_img longadder.png longadder %}
<!-- more -->

# LongAdder add 源码分析

因为继承自Striped64，因此LongAdder使用了
```java
transient volatile Cell[] cells;
transient volatile long base;
transient volatile int cellsBusy;
```
前情回顾：Striped64有3个核心变量，都是volatile修饰：
- base：计数字段
- cells：是一个Cell数组。使用lazy init方式。第一次访问时候初始化。
- cellsBusy：用于自旋锁，表明cells数组正在初始化或者扩容。0表示无cells竞争，1表示有线程在操作cells。

LongAdder核心是add()
```java
public void add(long x) {
    Cell[] as; long b, v; int m; Cell a;
    if ((as = cells) != null || !casBase(b = base, b + x)) {
        boolean uncontended = true;
        if (as == null || (m = as.length - 1) < 0 ||
            (a = as[getProbe() & m]) == null ||
            !(uncontended = a.cas(v = a.value, v + x)))
            longAccumulate(x, null, uncontended);
    }
}
```
第一个if：
- 如果cells不为空，则直接进入内层判断。（Striped64优先使用分段锁cells更新计数）
- 否则，cells为空，此时正在初始化，则尝试CAS更新base字段。如果成功则退出，否则进入内层判断。

第一个if虽然简单，但是值得细细品味。
然后乐观假设没有竞争uncontended=true，进入第二个if。

第二个if：
- 如果cells为空，或者未初始化完成（`(m = as.length - 1) < 0`），直接进入Striped64.longAccumulate()
- 否则，cells已经初始化，随机找一个cells的槽位（），且未被使用（`(a = as[getProbe() & m]) == null`），也是槽位没有竞争，直接进入Striped64.longAccumulate()
- 如果上一步随机探测的cell已经存在，则尝试在这个槽位CAS更新计数（`a.cas(v = a.value, v + x)`）。如果更新失败，则表明这个槽位有竞争，同时更新uncontended=true，进入Striped64.longAccumulate()

具体的Striped64.longAccumulate()就不在重复了。

# LongAdder sum 源码分析

显然计数存在于base和cells数组。
真实的计数=base + sum (cells)
```java
public long sum() {
    Cell[] as = cells; Cell a;
    long sum = base;
    if (as != null) {
        for (int i = 0; i < as.length; ++i) {
            if ((a = as[i]) != null)
                sum += a.value;
        }
    }
    return sum;
}
```
**因为这个方法没有加锁，不是并发安全的。**
javadoc上就有温馨提示：
>The returned value is <em>NOT</em> anatomic snapshot

# LongAdder reset 源码分析

resetfangf重置base和cells。可以复用LongAdder对象。同样，这个方法也不是线程安全的。个人感觉用途不大。
```java
public void reset() {
    Cell[] as = cells; Cell a;
    base = 0L;
    if (as != null) {
        for (int i = 0; i < as.length; ++i) {
            if ((a = as[i]) != null)
                a.value = 0L;
        }
    }
}
```

# LongAdder SerializationProxy

从类图可以看到，LongAdder实现了Serializable接口。但是LongAdder本身没有数据变量，所有属性来自父类Striped64。
```java
transient volatile Cell[] cells;
transient volatile long base;
transient volatile int cellsBusy;
```
Striped64中这几个变量都是non-public。不应该暴露这几个变量。同时，真正想要序列化的是真实的计数(当然只是snapshot)。因此LongAdder设计了内部类SerializationProxy，用于序列化和反序列化。
```java
private static class SerializationProxy implements Serializable {
    private static final long serialVersionUID = 7249069246863182397L;
    /**
     * The current value returned by sum().
     * @serial
     */
    private final long value;
    SerializationProxy(LongAdder a) {
        value = a.sum();
    }

    private Object readResolve() {
        LongAdder a = new LongAdder();
        a.base = value;
        return a;
    }    
}
```
直接sum计算当前计数。

Serializable接口的类支持使用readObject提供自定义的反序列化方式。这里直接返回异常，强调要使用SerializationProxy操作。
```java
private void readObject(java.io.ObjectInputStream s)
    throws java.io.InvalidObjectException {
    throw new java.io.InvalidObjectException("Proxy required");
}
```

# LongAdder vs AtomicLong

AtomicLong是乐观锁设计，CAS更新计数value。在多读少写的情况下性能好。
但是写竞争激烈的情况，乐观锁的前提就不存在了，导致大量更新线程自旋等待。
LongAdder继承自Striped64，使用了分段锁的设计、缓冲行填充优化，并发度更大，尽可能分散竞争。

写并发不高的情况下，AtomicLong已经够用了。

