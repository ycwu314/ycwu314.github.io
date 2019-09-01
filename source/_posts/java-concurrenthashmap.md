---
title: Java ConcurrentHashMap 原理
date: 2019-08-23 00:34:04
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [ConcurrentHashMap 详解]
description:
---

ConcurrentHashMap是并发安全的HashMap。ConcurrentHashMap设计比较复杂，涉及的知识比较多，建议先看看：
- {% post_link java-hashmap %}
- {% post_link java-striped64 %}
- {% post_link java-longadder %}

同样以java8作为分析。

<!-- more -->

# ConcurrentHashMap 简介

类似HashMap，使用数组+链表+红黑树的方式实现。
负载因子loadfactor，初始化大小initialCapacity，默认容量DEFAULT_CAPACITY，链表转红黑树TREEIFY_THRESHOLD都和HashMap一样。

# ConcurrentHashMap数组

table（非扩容时使用）、nextTable（扩容时使用）都使用volatile修饰，保证并发修改的可见性，关于volatile，见
- {% post_link java-volatile %}

```java
transient volatile Node<K,V>[] table;
private transient volatile Node<K,V>[] nextTable;
```
为了操作table、nextTable，使用Unsafe类提供的getObjectVolatile、putObjectVolatile等方法。
```java
@SuppressWarnings("unchecked")
static final <K,V> Node<K,V> tabAt(Node<K,V>[] tab, int i) {
    return (Node<K,V>)U.getObjectVolatile(tab, ((long)i << ASHIFT) + ABASE);
}

static final <K,V> boolean casTabAt(Node<K,V>[] tab, int i,
                                    Node<K,V> c, Node<K,V> v) {
    return U.compareAndSwapObject(tab, ((long)i << ASHIFT) + ABASE, c, v);
}

static final <K,V> void setTabAt(Node<K,V>[] tab, int i, Node<K,V> v) {
    U.putObjectVolatile(tab, ((long)i << ASHIFT) + ABASE, v);
}
```

# ConcurrentHashMap Node

```java
static class Node<K,V> implements Map.Entry<K,V> {
    final int hash;
    final K key;
    volatile V val;
    volatile Node<K,V> next;
}
```
Node的结构和HashMap.Node相似，但是val和next都使用volatile修饰，保证并发修改的可见性。
hash字段存放节点的哈希值。ConcurrentHashMap定义了几个特殊值：
```java
/*
 * Encodings for Node hash fields. See above for explanation.
 */
static final int MOVED     = -1; // hash for forwarding nodes
static final int TREEBIN   = -2; // hash for roots of trees
static final int RESERVED  = -3; // hash for transient reservations
static final int HASH_BITS = 0x7fffffff; // usable bits of normal node hash
```
MOVED、TREEBIN、RESERVED是为了对应的特殊节点使用。HASH_BITS是普通节点计算哈希时使用。

## ForwardingNode

ForwardingNode，扩容的时候使用。hash值为MOVED（-1）。
```java
/**
 * A node inserted at head of bins during transfer operations.
 */
static final class ForwardingNode<K,V> extends Node<K,V> {
    final Node<K,V>[] nextTable;
    ForwardingNode(Node<K,V>[] tab) {
        super(MOVED, null, null, null);
        this.nextTable = tab;
    }
}
```

## TreeBin

TreeBin是红黑树，对应hash值为TREEBIN（-2）。

## ReservationNode

ReservationNode在computeIfAbsent时候使用，对应hash为RESERVED（-3）。因为是占位符，不需要具体的key、value。
```java
/**
 * A place-holder node used in computeIfAbsent and compute
 */
static final class ReservationNode<K,V> extends Node<K,V> {
    ReservationNode() {
        super(RESERVED, null, null, null);
    }
}
```

# ConcurrentHashMap计算hash

同HashMap一样，为了定位key在table[]哪个位置，先做哈希计算。
计算hash的方式和HashMap类似，都会使用`(h ^ (h >>> 16))`，兼顾速度和降低冲突；但是ConcurrentHashMap多了一次对HASH_BITS按位与。
```java
    static final int spread(int h) {
        return (h ^ (h >>> 16)) & HASH_BITS;
    }
```
上面提到，HASH_BITS是普通节点使用。

# ConcurrentHashMap put()

1. key或者value不能为null
```java
if (key == null || value == null) throw new NullPointerException();
```

2. 计算hash
```java
int hash = spread(key.hashCode());
```

3. 遍历table，定位key的位置。
table[]和nextTable[]都是volatile修饰，这里使用Unsafe类直接访问指定槽位的内存数据
如果指定槽位为null，那么尝试cas方式插入节点
```java
if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
                if (casTabAt(tab, i, null,
                             new Node<K,V>(hash, key, value, null)))
                    break;                   // no lock when adding to empty bin
            }
```
如果正在resize，则参与扩容（扩容细节先按下不表）
```java
if ((fh = f.hash) == MOVED)
                tab = helpTransfer(tab, f);
```
否则，对该槽位加锁。然后根据链表或者红黑树方式更新value。
留意这里使用synchronized方式加锁，并且再次检查节点的hash
```java
V oldVal = null;
// 使用synchronized方式加锁
synchronized (f) {
    // 如果槽位已经不是节点f，则不做处理
    if (tabAt(tab, i) == f) {
        // fh > 0，是普通节点，并且是链表形式
        if (fh >= 0) {
            // 在链表分支中，binCount统计已经查找的节点数量
            // 如果该链表访问的节点数量到达TREEIFY_THRESHOLD，则进行转换
            binCount = 1;
            for (Node<K,V> e = f;; ++binCount) {
                K ek;
                if (e.hash == hash &&
                    ((ek = e.key) == key ||
                     (ek != null && key.equals(ek)))) {
                    oldVal = e.val;
                    if (!onlyIfAbsent)
                        e.val = value;
                    break;
                }
                Node<K,V> pred = e;
                if ((e = e.next) == null) {
                    pred.next = new Node<K,V>(hash, key,
                                              value, null);
                    break;
                }
            }
        }
        // 否则，是特殊节点，检查是否红黑树
        else if (f instanceof TreeBin) {
            Node<K,V> p;
            binCount = 2;
            if ((p = ((TreeBin<K,V>)f).putTreeVal(hash, key,
                                           value)) != null) {
                oldVal = p.val;
                if (!onlyIfAbsent)
                    p.val = value;
            }
        }
    }
}
```

4. 检查是否进行链表转换红黑树
```java
if (binCount != 0) {
    if (binCount >= TREEIFY_THRESHOLD)
        treeifyBin(tab, i);
    if (oldVal != null)
        return oldVal;
    break;
}
```
5. 更新计数，可能发生扩容。具体在后面再说
```java
addCount(1L, binCount);
```

小结：
- ConcurrentHashMap并发修改，如果table[x]是null则尝试CAS方式放入新节点，否则通过对table[x]槽位同步（synchronized）来实现线程安全。
- 标记table[x]正在扩容的方式是，table[x]节点的hash修改为MOVED
- ConcurrentHashMap支持多个线程参与table[x]的扩容helpTransfer()

# ConcurrentHashMap get()

```java
public V get(Object key) {
    Node<K,V>[] tab; Node<K,V> e, p; int n, eh; K ek;
    int h = spread(key.hashCode());
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (e = tabAt(tab, (n - 1) & h)) != null) {
        // 槽位的第一个节点
        if ((eh = e.hash) == h) {
            if ((ek = e.key) == key || (ek != null && key.equals(ek)))
                return e.val;
        }
        // 该节点处于特殊状态，（MOVED、RESERVED），或者是红黑树
        else if (eh < 0)
            return (p = e.find(h, key)) != null ? p.val : null;
        // 普通节点，且是链表，遍历该槽位的所有节点
        while ((e = e.next) != null) {
            if (e.hash == h &&
                ((ek = e.key) == key || (ek != null && key.equals(ek))))
                return e.val;
        }
    }
    return null;
}
```
ConcurrentHashMap支持并发修改，因此get的时候，某个槽位可能处于特殊状态（MOVED、RESERVED），或者是红黑树，因此使用Node提供的find方法遍历。
```java
static class Node<K,V> implements Map.Entry<K,V> {
    /**
     * Virtualized support for map.get(); overridden in subclasses.
     */
    Node<K,V> find(int h, Object k) {
        Node<K,V> e = this;
        if (k != null) {
            do {
                K ek;
                if (e.hash == h &&
                    ((ek = e.key) == k || (ek != null && k.equals(ek))))
                    return e;
            } while ((e = e.next) != null);
        }
        return null;
    }
}
```
Node的子类会覆盖find。

TreeNode使用红黑树方式查找
```java
static final class TreeNode<K,V> extends Node<K,V> {
    Node<K,V> find(int h, Object k) {
        return findTreeNode(h, k, null);
    }
}
```
ReservationNode用在computeIfAbsent，只是占位符，因此直接返null。
```java
static final class ReservationNode<K,V> extends Node<K,V> {
    Node<K,V> find(int h, Object k) {
        return null;
    }
}
```
ForwardingNode表明该位置正在发生resize。遍历的时候可能遇上节点也在做resize，Java实现上使用循环+代码块跳转，避免陷入多层递归。
```java
static final class ForwardingNode<K,V> extends Node<K,V> {
    final Node<K,V>[] nextTable;
    ForwardingNode(Node<K,V>[] tab) {
        super(MOVED, null, null, null);
        this.nextTable = tab;
    }
    Node<K,V> find(int h, Object k) {
        // loop to avoid arbitrarily deep recursion on forwarding nodes
        outer: for (Node<K,V>[] tab = nextTable;;) {
            Node<K,V> e; int n;
            if (k == null || tab == null || (n = tab.length) == 0 ||
                (e = tabAt(tab, (n - 1) & h)) == null)
                return null;
            for (;;) {
                int eh; K ek;
                if ((eh = e.hash) == h &&
                    ((ek = e.key) == k || (ek != null && k.equals(ek))))
                    return e;
                // 特殊状态的节点
                if (eh < 0) {
                    // 遇到ForwardingNode，则跳出当前循环，避免递归
                    if (e instanceof ForwardingNode) {
                        tab = ((ForwardingNode<K,V>)e).nextTable;
                        continue outer;
                    }
                    else
                        return e.find(h, k);
                }
                if ((e = e.next) == null)
                    return null;
            }
        }
    }
}
```
get方法小结：
- 不需要加锁

# ConcurrentHashMap computeIfAbsent()

computeIfAbsent: 如果没有对应的key，则执行mappingFunction计算，**并且保证最多只计算一次**。
```java
public V computeIfAbsent(K key, Function<? super K, ? extends V> mappingFunction)
```
考虑并发线程使用computeIfAbsent对同一个key操作。那么正常情况下，mappingFunction只被计算一次。
从执行mappingFunction得到value，到新建node保存key-value，不是原子化操作，因此要有机制实现。

ConcurrentHashMap的设计是：
1. 目标槽位为null：CAS设置一个占位符，使用了ReservationNode。
```java
if ((f = tabAt(tab, i = (n - 1) & h)) == null) {
    Node<K,V> r = new ReservationNode<K,V>();
    synchronized (r) {
        if (casTabAt(tab, i, null, r)) {
            binCount = 1;
            Node<K,V> node = null;
            try {
                if ((val = mappingFunction.apply(key)) != null)
                    node = new Node<K,V>(h, key, val, null);
            } finally {
                setTabAt(tab, i, node);
            }
        }
}
```
2. 目标槽位不为null：对这个槽位加锁
```java
synchronized (f) {
    // 分开链表、红黑树操作
}
```

小结：
- ReservationNode用于computeIfAbsent，当目标槽位为null时作为占位符。

# ConcurrentHashMap 扩容机制： transfer & helpTransfer

ConcurrentHashMap的扩容机制相对HashMap更加复杂。
ConcurrentHashMap的扩容，也是新建newTable，然后把原来table元素搬运到到newTable。但是这个搬运动作是并发！默认并发度是16（MIN_TRANSFER_STRIDE）。
```java
private static final int MAX_RESIZERS = (1 << (32 - RESIZE_STAMP_BITS)) - 1;
/**
 * The number of bits used for generation stamp in sizeCtl.
 * Must be at least 6 for 32bit arrays.
 */
private static int RESIZE_STAMP_BITS = 16;
/**
 * Minimum number of rebinnings per transfer step. Ranges are
 * subdivided to allow multiple resizer threads.  This value
 * serves as a lower bound to avoid resizers encountering
 * excessive memory contention.  The value should be at least
 * DEFAULT_CAPACITY.
 */
private static final int MIN_TRANSFER_STRIDE = 16;
```
除了上面3个和并发度相关的参数，还有sizeCtl变量
```java
/**
 * Table initialization and resizing control.  When negative, the
 * table is being initialized or resized: -1 for initialization,
 * else -(1 + the number of active resizing threads).  Otherwise,
 * when table is null, holds the initial table size to use upon
 * creation, or 0 for default. After initialization, holds the
 * next element count value upon which to resize the table.
 */
private transient volatile int sizeCtl;
```
sizeCtl:
- -1：正在初始化
- 其他负数：有N-1个线程正在进行扩容操作
- 0或者正数：table没有初始化；或者下一轮resize要调整的数量

和扩容相关的方法是transfer和helpTransfer。

TODO: 具体扩容比较复杂，先挖个坑，以后单独文章介绍。

# ConcurrentHashMap 获取大小 

获取容量大小有2个方法：
- size：java集合类覆盖的方法。返回int
- mappingCount：java8以后新增的。返回long。推荐使用此方法。
```java
public int size() {
    long n = sumCount();
    return ((n < 0L) ? 0 :
            (n > (long)Integer.MAX_VALUE) ? Integer.MAX_VALUE :
            (int)n);
}

/**
 * Returns the number of mappings. This method should be used
 * instead of {@link #size} because a ConcurrentHashMap may
 * contain more mappings than can be represented as an int. The
 * value returned is an estimate; the actual count may differ if
 * there are concurrent insertions or removals.
 *
 * @return the number of mappings
 * @since 1.8
 */
public long mappingCount() {
    long n = sumCount();
    return (n < 0L) ? 0L : n; // ignore transient negative values
}
```
不管是size还是mappingCount，都会使用sumCount
```java
final long sumCount() {
    CounterCell[] as = counterCells; CounterCell a;
    long sum = baseCount;
    if (as != null) {
        for (int i = 0; i < as.length; ++i) {
            if ((a = as[i]) != null)
                sum += a.value;
        }
    }
    return sum;
}
```
如果counterCells不为null，则遍历counterCells，把value加上到baseCount。否则直接返回baseCount。
疑问：
- baseCount的用途？在什么时候更新？
- counterCells是什么？在什么时候更新？

先看baseCount，在没有竞争的情况下使用，通过CAS方式更新。BASECOUNT在addCount和fullAddCount使用。
```java
/**
 * Base counter value, used mainly when there is no contention,
 * but also as a fallback during table initialization
 * races. Updated via CAS.
 */
private transient volatile long baseCount;

BASECOUNT = U.objectFieldOffset
    (k.getDeclaredField("baseCount"));
```

CounterCell用来做发生冲突时的计数。还有个关联的cellsBusy变量，表示正在使用自旋锁更新counterCells。
```java
 /**
  * Spinlock (locked via CAS) used when resizing and/or creating CounterCells.
  */
 private transient volatile int cellsBusy;
 /**
  * Table of counter cells. When non-null, size is a power of 2.
  */
 private transient volatile CounterCell[] counterCells;
```
CounterCell的数据结构很简单，只有一个long类型的value保存计数。但是使用了`@sun.misc.Contended`注解，同时javadoc表示从LongAdder和Striped64改造。这里先不做扩展。
```java
/**
 * A padded cell for distributing counts.  Adapted from LongAdder
 * and Striped64.  See their internal docs for explanation.
 */
@sun.misc.Contended static final class CounterCell {
    volatile long value;
    CounterCell(long x) { value = x; }
}
```
在ide中查找引用，发现只在fullAddCount方法修改counterCells
{% asset_img fullAddCount.PNG fullAddCount %}
fullAddCount又有温馨提示了，具体要看LongAdder的设计。
```java
// See LongAdder version for explanation
private final void fullAddCount(long x, boolean wasUncontended) {
```
Striped64、LongAdder文章：
- {% post_link java-striped64 %}
- {% post_link java-longadder %}

fullAddCount被addCount调用。
```java
/**
 * Adds to count, and if table is too small and not already
 * resizing, initiates transfer. If already resizing, helps
 * perform transfer if work is available.  Rechecks occupancy
 * after a transfer to see if another resize is already needed
 * because resizings are lagging additions.
 *
 * @param x the count to add
 * @param check if <0, don't check resize, if <= 1 only check if uncontended
 */
private final void addCount(long x, int check) {
    CounterCell[] as; long b, s;
    // 如果有可用的counterCells，并且CAS更新baseCount失败，
    if ((as = counterCells) != null ||
        !U.compareAndSwapLong(this, BASECOUNT, b = baseCount, s = b + x)) {
        CounterCell a; long v; int m;
        boolean uncontended = true;

        if (as == null || (m = as.length - 1) < 0 ||                        // 检查counterCells是否可用
            (a = as[ThreadLocalRandom.getProbe() & m]) == null ||           // 随机找一个可用（即null）的counterCell槽位
            !(uncontended =
              U.compareAndSwapLong(a, CELLVALUE, v = a.value, v + x))) {    // 并且在该槽位上更新失败
            fullAddCount(x, uncontended);                                   // 则执行fullAddCount
            return;
        }
        // 执行此处，表明已经CAS更新了counterCell
        if (check <= 1)
            return;
        s = sumCount();
    }
    // 需要resize。这里先不深入
    if (check >= 0) {
        Node<K,V>[] tab, nt; int n, sc;
        while (s >= (long)(sc = sizeCtl) && (tab = table) != null &&
               (n = tab.length) < MAXIMUM_CAPACITY) {
            int rs = resizeStamp(n);
            if (sc < 0) {
                if ((sc >>> RESIZE_STAMP_SHIFT) != rs || sc == rs + 1 ||
                    sc == rs + MAX_RESIZERS || (nt = nextTable) == null ||
                    transferIndex <= 0)
                    break;
                if (U.compareAndSwapInt(this, SIZECTL, sc, sc + 1))
                    transfer(tab, nt);
            }
            else if (U.compareAndSwapInt(this, SIZECTL, sc,
                                         (rs << RESIZE_STAMP_SHIFT) + 2))
                transfer(tab, null);
            s = sumCount();
        }
    }
}
```
addCount小结：
- 尝试CAS更新baseCount。如果有竞争，则使用fullAddCount。
- fullAddCount参考了LongAdder的设计

# ConcurrentHashMap 并发度

ConcurrentHashMap大量使用CAS更新，只有失败才进行同步。从上面代码可见，同步的位置是table[x]。因此并发度是table的长度。

# Java7的ConcurrentHashMap

HashMap、ConcurrentHashMap都在Java8增加了链表转红黑树，设计复杂了。
对比[Java 7 ConcurrentHashMap.java](http://hg.openjdk.java.net/jdk7/jdk7/jdk/file/9b8c96f96a0f/src/share/classes/java/util/concurrent/ConcurrentHashMap.java)，Java8的Java7中的Segment数组对应Java8中table数组。但是真实数据存放在HashEntry类型的table数组。
```java
final Segment<K,V>[] segments;
static final class Segment<K,V> extends ReentrantLock implements Serializable {
    transient volatile HashEntry<K,V>[] table;
}
```
每个Segment就是一个ReentrantLock。如果要加锁，直接使用ReentrantLock.lock。
在Java8，要对槽位加锁，使用synchronized。

我的理解是：
1. Java对synchronized优化，和ReentrantLock相差越来越少
2. 随着ConcurrentHashMap扩容，并发度越大，单个槽位的竞争变少
3. ConcurrentHashMap把所有节点（链表节点、红黑树、特殊状态节点）都抽象统一为Node类型，槽位也能直接存放数组，并且优先使用CAS更新。CAS要比ReentrantLock更加轻量。
4. 如果使用继续使用ReentrantLock，那么消耗大量存储空间（ReentrantLock底层使用AQS。同时所有Node都变成了ReentrantLock，完全没有这个必要）。

# ConcurrentHashMap 小结

- ConcurrentHashMap不支持key或者value为null。
- ConcurrentHashMap的并发度是table[]的长度，默认是16。背后的设计思路是优先CAS更新、失败则使用synchronized加锁（缩小加锁范围）。
- ConcurrentHashMap并发扩容使用sizeCtl控制
- ConcurrentHashMap有3种特殊类型的节点：TreeNode（红黑树），ReservationNode（用于computeIfAbsent的占位符），ForwardingNode（resize标记）
- ConcurrentHashMap可以使用size或者mappingCount获取容量大小。java8以后推荐使用mappingCount方法。
- CounterCell保存在竞争条件下CAS更新baseCount失败的计数
- 计数更新：使用addCount()尝试CAS更新baseCount，如果失败则使用fullAddCount()。
- fullAddCount设计参考了LongAdder

ConcurrentHashMap值得反复品味的设计细节很多。

# 参考

- [ConcurrentHashMap扩容源码介绍](https://kkewwei.github.io/elasticsearch_learning/2017/11/14/ConcurrentHashMap%E6%89%A9%E5%AE%B9%E8%BF%87%E7%A8%8B%E4%BB%8B%E7%BB%8D/)
- [1.8版本的ConcurrentHashMap分析](http://footmanff.com/2018/03/13/2018-03-13-ConcurrentHashMap-1/)

