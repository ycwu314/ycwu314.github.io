---
title: Java 8 HashMap详解
date: 2019-08-23 10:23:42
tags: [java]
categories: [java]
keywords: [hashmp 原理, hashmap loadfactor, HashMap modCount, ConcurrentModificationException, hashmap 死循环]
description:  Java 8 HashMap使用数据+链表+红黑树的结构。HashMap不是线程安全的，使用modCount字段实现fail-fast机制。遍历HashMap同时发生修改，抛出ConcurrentModificationException。Java8之前的HashMap容易在并发条件发生死循环。
---

HashMap是一个常用的key-value工具。这里以java8版本介绍。

# Java8 HashMap 简介

{% asset_img hashmap.png %}
Java8 HashMap采用数组（Java8是`Node<K,V>[] table`，Java8之前是`Entry[] table`）+链表+红黑树的方式实现。
对于key做hash，得到所在的数组位置。
hash可能发生冲突，即多个key都hash到同一个数组位置（桶，bucket）。HashMap采用拉链法处理冲突，也就是数组位置存放链表，所有冲突的key都在这个链表。通过遍历可以找到目标key和value。
但是有些情况下，可能大量的key都冲突到同一个bucket，导致链表很长。这样遍历查找key耗时长，时间复杂度为 O(N)。
为了解决这个问题，如果一个bucket的链表长度超过一定长度，则转换为红黑树。

<!-- more -->

# HashMap Node

HashMap包含了内部类Node作为基本节点结构。
```java
static class Node<K,V> implements Map.Entry<K,V> {
    final int hash;
    final K key;
    V value;
    Node<K,V> next;
}
```
上面提到链表长度达到阈值（TREEIFY_THRESHOLD），会触发转为红黑树。因此HashMap也定义了红黑树Node
```java
static final class TreeNode<K,V> extends LinkedHashMap.Entry<K,V> {
    TreeNode<K,V> parent;  // red-black tree links
    TreeNode<K,V> left;
    TreeNode<K,V> right;
    TreeNode<K,V> prev;    // needed to unlink next upon deletion
    boolean red;
}
```
两者Node关系见下图
{% asset_img hashmap-entry.png %}

# HashMap loadfactor

table数组越满，哈希发生冲突的概率就越高。一旦发生冲突，就要遍历链表或者从红黑树查找key。提高hashmap性能的方式是，不要写满、保留适当的空间。
loadfactor描述hashmap的负载情况，默认是0.75f。可以在构造函数指定。
```java
static final float DEFAULT_LOAD_FACTOR = 0.75f;

public HashMap(int initialCapacity, float loadFactor){
    // more code
    this.loadFactor = loadFactor;
    this.threshold = tableSizeFor(initialCapacity);    
}
```

# HashMap初始化大小

上面的构造函数`HashMap(int initialCapacity, float loadFactor)`可以传入initialCapacity作为初始化容量。
但这不是真正的初始化容量，HashMap会做调整，调整为比initialCapacity大的2整数幂（见tableSizeFor函数）。
比如initialCapacity=14，则threshold调整为16。
如果不指定，默认为初始化大小为16（DEFAULT_INITIAL_CAPACITY）。
```java
/**
 * The next size value at which to resize (capacity * load factor).
 *
 * @serial
 */
int threshold;

static final int DEFAULT_INITIAL_CAPACITY = 1 << 4; // aka 16

/**
 * Returns a power of two size for the given target capacity.
 */
static final int tableSizeFor(int cap) {
    int n = cap - 1;
    n |= n >>> 1;
    n |= n >>> 2;
    n |= n >>> 4;
    n |= n >>> 8;
    n |= n >>> 16;
    return (n < 0) ? 1 : (n >= MAXIMUM_CAPACITY) ? MAXIMUM_CAPACITY : n + 1;
}
```
为什么要做初始化大小调整呢？前面提到loadfactor，保持未用空间比例。如果发生大小调整，2的整数幂做重新哈希会相当方便。

ps. 阿里巴巴Java开发手册其中一条规定是，使用HashMap，要指定初始化容量大小。

顺带提下，HashMap的最大容量限制是
```java
static final int MAXIMUM_CAPACITY = 1 << 30;
```

# HashMap put()

向hashmap添加key-value，先计算这个key的hash值，最终调用putVal方法。
```java
public V put(K key, V value) {
    return putVal(hash(key), key, value, false, true);
}
```

```java
final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
               boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;
    // lazy init
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;
    // table[]对应槽位为null，直接把key放在这个位置
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);
    else {
        Node<K,V> e; K k;
        // 如果该槽位第一个元素是目标key，返回该节点
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            e = p;
        // 如果该槽位第一个元素是TreeNode，则放到红黑树
        else if (p instanceof TreeNode)
            e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
        else {
            // 否则，是链表结构，则遍历
            for (int binCount = 0; ; ++binCount) {
                // 没有找到已有元素，则插入到链表尾部
                if ((e = p.next) == null) {
                    p.next = newNode(hash, key, value, null);
                    // 链表增加新元素后，可能到达treeify的下限
                    if (binCount >= TREEIFY_THRESHOLD - 1) // -1 for 1st
                        treeifyBin(tab, hash);
                    break;
                }
                // 在链表中找到已有元素，返回该节点
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    break;
                p = e;
            }
        }
        // 找到已有节点，更新value
        if (e != null) { // existing mapping for key
            V oldValue = e.value;
            if (!onlyIfAbsent || oldValue == null)
                e.value = value;
            afterNodeAccess(e);
            return oldValue;
        }
    }
    ++modCount;
    // 新增元素，检查触发扩容
    if (++size > threshold)
        resize();
    afterNodeInsertion(evict);
    return null;
}
```
putTreeVal、treeifyBin是红黑树相关操作，这里不做展开。

HashMap源码还有afterNodeXXX方法，是留给LinkedHashMap使用，同样先不做展开。
```java
// Callbacks to allow LinkedHashMap post-actions
void afterNodeAccess(Node<K,V> p) { }
void afterNodeInsertion(boolean evict) { }
void afterNodeRemoval(Node<K,V> p) { }
```

# HashMap get()

get()底层使用getNode
```java
public V get(Object key) {
    Node<K,V> e;
    return (e = getNode(hash(key), key)) == null ? null : e.value;
}
```

```java
final Node<K,V> getNode(int hash, Object key) {
    Node<K,V>[] tab; Node<K,V> first, e; int n; K k;
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (first = tab[(n - 1) & hash]) != null) {
        // 先检查第一个槽位的元素
        if (first.hash == hash && // always check first node
            ((k = first.key) == key || (key != null && key.equals(k))))
            return first;
        if ((e = first.next) != null) {
            // 访问红黑树
            if (first instanceof TreeNode)
                return ((TreeNode<K,V>)first).getTreeNode(hash, key);
            do {
                // 遍历链表
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    return e;
            } while ((e = e.next) != null);
        }
    }
    return null;
}
```

# HashMap remove

remove从HashMap中查找并且删除元素。
```java
final Node<K,V> removeNode(int hash, Object key, Object value,
                           boolean matchValue, boolean movable) {
    Node<K,V>[] tab; Node<K,V> p; int n, index;
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (p = tab[index = (n - 1) & hash]) != null) {
        Node<K,V> node = null, e; K k; V v;
        // 先检查槽位的第一个元素
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            node = p;
        else if ((e = p.next) != null) {
            // 查找红黑树
            if (p instanceof TreeNode)
                node = ((TreeNode<K,V>)p).getTreeNode(hash, key);
            else {
                // 链表查找
                do {
                    if (e.hash == hash &&
                        ((k = e.key) == key ||
                         (key != null && key.equals(k)))) {
                        node = e;
                        break;
                    }
                    p = e;
                } while ((e = e.next) != null);
            }
        }
        // 找到节点，从红黑树或者链表删除
        if (node != null && (!matchValue || (v = node.value) == value ||
                             (value != null && value.equals(v)))) {
            if (node instanceof TreeNode)
                ((TreeNode<K,V>)node).removeTreeNode(this, tab, movable);
            else if (node == p)
                tab[index] = node.next;
            else
                p.next = node.next;
            ++modCount;
            --size;
            afterNodeRemoval(node);
            return node;
        }
    }
    return null;
}
```

# HashMap hash 深入

哈希函数的2个指标：
- 计算速度
- 冲突量

常见的hash方式是取模，但是HashMap实现并没有使用，而是设计了一个hash函数。

先看一眼Java8的hash
```java
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
```

这个hash函数对比简单的取模（`x % y`），好处在于：位运算比取模要快。

计算hash的目的是为了找到table[]中的槽位：
```java
p = tab[index = (n - 1) & hash]
```
n是table数组的长度。之前讲到，扩容的时候，table[]的大小是2的整数幂。其中包含一个数学特性
>X % 2^n = X & (2^n – 1)
>
>2^n表示2的n次方，也就是说，一个数对2^n取模 == 一个数和(2^n – 1)做按位与运算 。
>假设n为3，则2^3 = 8，表示成2进制就是1000。2^3 = 7 ，即0111。
>此时X & (2^3 – 1) 就相当于取X的2进制的最后三位数。
>从2进制角度来看，X / 8相当于 X >> 3，即把X右移3位，此时得到了X / 8的商，而被移掉的部分(后三位)，则是X % 8，也就是余数。

看一个例子就很直观
{% asset_img hash-mod.png %}

精心设计数组长度为2的整数幂，用位运算代替取模，解决了哈希计算的速度问题。哈希函数的另一个问题是冲突率。看下面的例子
{% asset_img hash-conflict.png %}
对于取模运算，冲突常见的是高位不同、低位相同。
解决冲突的思路是，进行扰动操作，把高位特征加入到hash当中。Java8的实现很简单，把h和h的高16位做异或（XOR）运算。
```java
(h = key.hashCode()) ^ (h >>> 16)
```
Java8之前的hash更加复杂
```java
final int hash(Object k) {
    int h = hashSeed;
    if (0 != h && k instanceof String) {
        return sun.misc.Hashing.stringHash32((String) k);
    }

    h ^= k.hashCode();
    h ^= (h >>> 20) ^ (h >>> 12);
    return h ^ (h >>> 7) ^ (h >>> 4);
}

static int indexFor(int h, int length) {
    return h & (length-1);
}
```

# HashMap resize 扩容机制

有了上面hash设计的基础，就方便理解HashMap扩容机制。
Java8的resize()负责扩容（double by 2）或者初始化table[]。扩容涉及的操作：
- 计算新的threshold、newCap
- 初始化新的newTab[]
- 把原来table的元素，重新哈希到newTab

因为table[]中的结构，可能是链表，也可能是红黑树，需要分开处理。
这里只分析链表情况，比较难理解的是重新hash过程。
```java
for (int j = 0; j < oldCap; ++j) {
    Node<K,V> e;
    if ((e = oldTab[j]) != null) {
        oldTab[j] = null;
        if (e.next == null)
            newTab[e.hash & (newCap - 1)] = e;
        else if (e instanceof TreeNode)
            // 拆分红黑树
            ((TreeNode<K,V>)e).split(this, newTab, j, oldCap);
        else { // preserve order
            // 链表情况
            // 拆分为lo链表和hi链表
            Node<K,V> loHead = null, loTail = null;
            Node<K,V> hiHead = null, hiTail = null;
            Node<K,V> next;
            do {
                next = e.next;
                // 划重点： (e.hash & oldCap) == 0
                if ((e.hash & oldCap) == 0) {
                    if (loTail == null)
                        loHead = e;
                    else
                        loTail.next = e;
                    loTail = e;
                }
                else {
                    if (hiTail == null)
                        hiHead = e;
                    else
                        hiTail.next = e;
                    hiTail = e;
                }
            } while ((e = next) != null);
            // 划重点
            if (loTail != null) {
                loTail.next = null;
                newTab[j] = loHead;
            }
            // 划重点
            if (hiTail != null) {
                hiTail.next = null;
                newTab[j + oldCap] = hiHead;
            }
        }
    }
}
```
分为lo链表、hi链表
```java
Node<K,V> loHead = null, loTail = null;
Node<K,V> hiHead = null, hiTail = null;
```
然后遍历这个槽位，把`(e.hash & oldCap) == 0`放入到lo链表，其他放到hi链表。
如果lo链表不为null，则把lo链表放到newTab[j]。
如果hi链表不为null，则把hi链表放到newTab[j + oldCap]。

为什么呢？逐步分析：
- hashmap的大小是2的整数幂。
- 假设oldCap=2^n，newCap是oldCap的2倍，则newCap=2^(n+1)。
- 又因为 X % 2^n = X & (2^n – 1)，则X对newCap求模，等于计算X的2进制的最后n+1位数。
- 为了计算新槽位的位置，就要 e.hash & newCap 。
- 不管计算 e.hash & oldCap 还是 e.hash & newCap，都可以转化为计算e.hash的二进制的低n位或者n+1位（newCap比oldCap多取一位）。 

假设e.hash & oldCap = xyz，那么 e.hash & newCap的结果，只能是
- 0xyz
- 1xyz

这2个结果相差一个oldCap（这里举例用oldCap=8）。
也就是说，计算新槽位，可以使用e.hash & oldCap代替。

因此
- e.hash & oldCap = 0，则在newTab[j]
- e.hash & oldCap ≠ 0，则在newTab[j+oldCap]

# 比较key

HashMap比较key是否相同，实现是
```java
p.hash == hash && ((k = p.key) == key || (key != null && key.equals(k)))
```
虽然简单，但是值得品味。

1. hash不同，肯定不是同一个key，直接返回false
2. 否则，比较key的引用（==），引用相同，肯定是同一个key，返回true
3. 使用key的equals方法比较

可以直接使用key的equals方法吗？可以的，但是equals方法通常比较重型，比较hash、引用，则更加轻便（fast path）。

# HashMap modCount 和 fail-fast

修改（get、put、remove）方法，都对modCount字段进行自增操作。先看介绍
```java
/**
 * The number of times this HashMap has been structurally modified
 * Structural modifications are those that change the number of mappings in
 * the HashMap or otherwise modify its internal structure (e.g.,
 * rehash).  This field is used to make iterators on Collection-views of
 * the HashMap fail-fast.  (See ConcurrentModificationException).
 */
transient int modCount;
```
modCount是为了支持fail-fast机制，能在第一时间感知集合的内部结构被修改。在Java中，fail-fast机制通常使用比较操作前后的modCount计数和抛出ConcurrentModificationException实现。
以HashMap.EntrySet.forEach()为例：
```java
public final void forEach(Consumer<? super Map.Entry<K,V>> action) {
    Node<K,V>[] tab;
    if (action == null)
        throw new NullPointerException();
    if (size > 0 && (tab = table) != null) {
        // 保存旧的modCount
        int mc = modCount;
        for (int i = 0; i < tab.length; ++i) {
            for (Node<K,V> e = tab[i]; e != null; e = e.next)
                action.accept(e);
        }
        // 当前modCount和旧的modCount不相同，则发生了并发修改。
        if (modCount != mc)
            throw new ConcurrentModificationException();
    }
}
```

# 并发问题

HashMap不是线程安全容器！
HashMap不是线程安全容器！
HashMap不是线程安全容器！
有并发需求，使用ConcurrentHashMap。

HashMap的并发问题，纯属使用不当的问题。
发生问题的代码是Java8之前。那时候的设计是数组+链表存储。并且扩容方式如下
```java
void resize(int newCapacity) {
    Entry[] oldTable = table;
    int oldCapacity = oldTable.length;
    if (oldCapacity == MAXIMUM_CAPACITY) {
        threshold = Integer.MAX_VALUE;
        return;
    }
    
    Entry[] newTable = new Entry[newCapacity];
    transfer(newTable);
    table = newTable;
    threshold = (int)(newCapacity * loadFactor);
}

/**
 * Transfers all entries from current table to newTable.
 */
void transfer(Entry[] newTable) {
    Entry[] src = table;
    int newCapacity = newTable.length;
    for (int j = 0; j < src.length; j++) {
        Entry<K,V> e = src[j];
        if (e != null) {
            src[j] = null;
            do {
                Entry<K,V> next = e.next;
                // rehash
                int i = indexFor(e.hash, newCapacity);
                // 并发条件下，可能在此处形成环形
                e.next = newTable[i];
                newTable[i] = e;
                e = next;
            // 因为形成环，所以永远 e != null，死循环
            } while (e != null);
        }
    }
}
```
resize的时候直接把所有元素rehash，然后搬运到newTable。
问题发生在
```java
e.next = newTable[i]
```
并发情况下，多个线程同时各自引发了resize，可能出现`next=e.next; e.next=newTalbe[i]=e`。
具体阅读这个文章：[疫苗：JAVA HASHMAP的死循环](https://coolshell.cn/articles/9606.html)

# HashMap 小结

- java8之前采用数组+链表的方式实现，通过链表处理冲突
- java8之后采用数组+链表+红黑树的方式实现
- HashMap不是线程安全的，使用modCount字段实现fail-fast机制
- HashMap的扩容方式是double by 2
- HashMap支持null作为key，实现上把null放在table[0]的第一个元素
- java8之前的HashMap有并发情况下死循环的问题。

# 参考

- [openjdk 6 HashMap](http://hg.openjdk.java.net/jdk6/jdk6/jdk/file/tip/src/share/classes/java/util/HashMap.java)
- [深入理解HashMap(四): 关键源码逐行分析之resize扩容](https://segmentfault.com/a/1190000015812438)

