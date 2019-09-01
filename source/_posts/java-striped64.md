---
title: Java Striped64 原理
date: 2019-08-24 23:30:26
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [Striped64 原理, longAccumulate]
description: Striped64是Java8新增的、64bit高性能累加器。Striped64是LongAdder、LongAccumulator等类的基类。
---

Striped64是Java8新增的、64bit高性能累加器。Striped64是LongAdder、LongAccumulator等类的基类。ConcurrentHashMap的计数就使用了Striped64和LongAdder的设计。
{% asset_img v1_striped64.png striped64 %}

<!-- more -->

# Striped64 初探

Striped64是个抽象类，为子类提供工具方法支持。
Striped64有3个核心变量，都是volatile修饰：
- base：计数字段
- cells：是一个Cell数组。使用lazy init方式。第一次访问时候初始化。
- cellsBusy：用于自旋锁，表明cells数组正在初始化或者扩容。0表示无cells竞争，1表示有线程在操作cells。

```java
abstract class Striped64 extends Number {
    /**
     * Table of cells. When non-null, size is a power of 2.
     */
    transient volatile Cell[] cells;

    /**
     * Base value, used mainly when there is no contention, but also as
     * a fallback during table initialization races. Updated via CAS.
     */
    transient volatile long base;

    /**
     * Spinlock (locked via CAS) used when resizing and/or creating Cells.
     */
    transient volatile int cellsBusy;
}
```

Striped64设计思路：
- 优先把计数更新到cells数组。
- 每次遇到竞争，则扩容为2倍，直到等于cpu核数，或者比cpu核数大的、最小的2的整数幂。使用cellsBusy自旋锁。
- 最后才尝试CAS更新base

# Striped64 Cell

```java
@sun.misc.Contended static final class Cell {
        volatile long value;
```
Cell核心是一个long容器。注意被Contended注解修饰。在Java 8中，提供了@sun.misc.Contended注解来避免缓存伪共享。具体可以看看：
- {% post_link java-contended-avoid-false-sharing %}

cells数组扩容是有限制的。原因是使用随机探针方式试探cells的冲突，只有CAS失败才知道。更大的cells会影响收敛时间。
cells数组不考虑回收问题，因为在常时间运行、高并发环境，这些cells最终会有机会使用。
```java
/*
 * The table size is capped because, when there are more threads
 * than CPUs, supposing that each thread were bound to a CPU,
 * there would exist a perfect hash function mapping threads to
 * slots that eliminates collisions. When we reach capacity, we
 * search for this mapping by randomly varying the hash codes of
 * colliding threads.  Because search is random, and collisions
 * only become known via CAS failures, convergence can be slow,
 * and because threads are typically not bound to CPUS forever,
 * may not occur at all. However, despite these limitations,
 * observed contention rates are typically low in these cases.
 *
 * It is possible for a Cell to become unused when threads that
 * once hashed to it terminate, as well as in the case where
 * doubling the table causes no thread to hash to it under
 * expanded mask.  We do not try to detect or remove such cells,
 * under the assumption that for long-running instances, observed
 * contention levels will recur, so the cells will eventually be
 * needed again; and for short-lived ones, it does not matter.
 */
```

# Striped64 PROBE / threadLocalRandomProbe

发生竞争时候，使用cells数组存储计数。那么有个问题，选择cells的哪个位置存储呢？答案是Thread类的threadLocalRandomProbe变量。
Thread.java
```java
/** Probe hash value; nonzero if threadLocalRandomSeed initialized */
@sun.misc.Contended("tlr")
int threadLocalRandomProbe;
```

Striped64使用unsafe操作Thread类的threadLocalRandomProbe变量
```java
private static final long PROBE;

    static {
    try {
        // more code
        Class<?> tk = Thread.class;
        PROBE = UNSAFE.objectFieldOffset
            (tk.getDeclaredField("threadLocalRandomProbe"));
    }
```

每次计算PROBE的位置，都使用ThreadLocalRandom的伪随机算法。
```java
/**
 * Pseudo-randomly advances and records the given probe value for the
 * given thread.
 * Duplicated from ThreadLocalRandom because of packaging restrictions.
 */
static final int advanceProbe(int probe) {
    probe ^= probe << 13;   // xorshift
    probe ^= probe >>> 17;
    probe ^= probe << 5;
    UNSAFE.putInt(Thread.currentThread(), PROBE, probe);
    return probe;
}

// 返回当前线程的probe值
static final int getProbe() {
    return UNSAFE.getInt(Thread.currentThread(), PROBE);
}
```

# Striped64 longAccumulate 详解

有了前面的准备分析，可以深入了解Striped64实现。
Striped64提供了longAccumulate和doubleAccumulate两个工具方法（因为long和double是64bit）。这里研究longAccumulate。
```java
final void longAccumulate(long x, LongBinaryOperator fn,
                              boolean wasUncontended)
```
其中：
- x：要更新的值。
- fn：更新函数。null则直接增加x。为LongAdder提供支持。
- wasUncontended：无冲突标记。如果调用之前CAS操作失败，则为false。

如果当前线程的probe为0，则未初始化，初始化之，并且更新wasUncontended。
```java
int h;
if ((h = getProbe()) == 0) {
    ThreadLocalRandom.current(); // force initialization
    h = getProbe();
    // 没有冲突
    wasUncontended = true;
}
```

ThreadLocalRandom.current初始化当前线程的探针：
```java
public static ThreadLocalRandom current() {
    if (UNSAFE.getInt(Thread.currentThread(), PROBE) == 0)
        localInit();
    return instance;
}
```

接下来是重头戏，在循环中更新计数。if-else分支很多，直接在代码上做解析：
```java
for (;;) {
    Cell[] as; Cell a; int n; long v;
    // 如果有cells数组可用
    if ((as = cells) != null && (n = as.length) > 0) {
        // 当前线程哈希到cells数组，且未被使用，则尝试新建一个cell（lazy init）
        if ((a = as[(n - 1) & h]) == null) {
            // 尝试乐观锁方式更新
            if (cellsBusy == 0) {       // Try to attach new Cell
                Cell r = new Cell(x);   // Optimistically create
                // 再次检查cellsBusy，尝试cas更新
                if (cellsBusy == 0 && casCellsBusy()) {
                    boolean created = false;
                    try {               // Recheck under lock
                        Cell[] rs; int m, j;
                        if ((rs = cells) != null &&
                            (m = rs.length) > 0 &&
                            rs[j = (m - 1) & h] == null) {
                            rs[j] = r;
                            created = true;
                        }
                    } finally {
                        // 释放自旋锁
                        cellsBusy = 0;
                    }
                    if (created)
                        break;
                    continue;           // Slot is now non-empty
                }
            }
            collide = false;
        }
        // 已经有cell存在，如果之前是没有竞争，就要更新为有竞争，且在下一次循环继续
        else if (!wasUncontended)       // CAS already known to fail
            wasUncontended = true;      // Continue after rehash
        // 既然有cell，尝试在该cell cas更新计数，如果成功则跳出循环
        else if (a.cas(v = a.value, ((fn == null) ? v + x :
                                     fn.applyAsLong(v, x))))
            break;
        // CAS更新该cell失败了，有竞争
        // 如果cells数组长度到达最大值，或者已经改变，则进入下一轮循环的初始状态是没有冲突（是下一轮！）
        else if (n >= NCPU || cells != as)
            collide = false;            // At max size or stale
        // 如果之前检查没有冲突，则在进入下一轮循环的初始状态是有冲突
        else if (!collide)
            collide = true;
        // 到达这个分支的条件：cells有竞争，且容量未到最大值
        // 尝试获取乐观锁，并对cells扩容
        else if (cellsBusy == 0 && casCellsBusy()) {
            try {
                if (cells == as) {      // Expand table unless stale
                    Cell[] rs = new Cell[n << 1];
                    for (int i = 0; i < n; ++i)
                        rs[i] = as[i];
                    cells = rs;
                }
            } finally {
                cellsBusy = 0;
            }
            collide = false;
            continue;                   // Retry with expanded table
        }
        // 进入下一轮循环之前，更新探针
        h = advanceProbe(h);
    }
    // cells数组未初始化。进行lazy init
    else if (cellsBusy == 0 && cells == as && casCellsBusy()) {
        boolean init = false;
        try {                           // Initialize table
            if (cells == as) {
                Cell[] rs = new Cell[2];
                rs[h & 1] = new Cell(x);
                cells = rs;
                init = true;
            }
        } finally {
            cellsBusy = 0;
        }
        if (init)
            break;
    }
    // 进入此分支的条件：
    // 1. cells数组为null
    // 2. 无法初始化cells数组
    // 则尝试CAS更新base变量
    else if (casBase(v = base, ((fn == null) ? v + x :
                                fn.applyAsLong(v, x))))
        break;                          // Fall back on using base
}
```

# Striped64 总结

Striped64的核心思路是，尽量使用分段锁，提高并发度。只有在fallback情况才更新base计数器，并且是CAS方式。
Cell数组使用@Contended注解，避免缓存伪共享。

