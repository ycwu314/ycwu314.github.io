---
title: ThreadLocal原理
date: 2019-08-18 22:17:27
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [threadlocal 源码, ThreadLocal 内存泄露, expungeStaleEntry, replaceStaleEntry, ThreadLocalMap]
description: ThreadLocal是每个线程都能独立初始化、访问、修改的变量。ThreadLocal变量不是共享变量，不存在线程安全的问题，不需要同步。ThreadLocalMap的key是ThreadLocal类型，并且继承WeakReference。为了避免内存泄露，ThreadLocalMap的get、set、remove操作，对应key==null的情况，触发expungeStaleEntry清理。
---

# ThreadLocal是什么

ThreadLocal的字面意思是“线程本地变量”，即每个线程都能独立初始化、访问、修改这个变量，因此才叫thread local。javadoc对ThreadLocal类的简介：
>This class provides thread-local variables. These variables differ from their normal counterparts in that each thread that accesses one (via its get or set method) has its own, independently initialized copy of the variable. 

因为ThreadLocal变量是每个线程独自拥有、相互隔离，因此**ThreadLocal变量不是共享变量，不存在线程安全的问题，不需要同步**。

<!-- more -->

# ThreadLocal应用场景

javadoc提及了ThreadLocal的一些应用场景
>ThreadLocal instances are typically private static fields in classes that wish to associate state with a thread (e.g., a user ID or Transaction ID).

1. 隐式传参。例如一个线程处理周期中，会反复使用的变量，例如用户Id、事务Id，直接放在ThreadLocal，要比每个使用方法增加userId、transactionId要简洁。
2. 事务处理也经常使用ThreadLocal，参见 [TransactionSynchronizationManager](https://github.com/spring-projects/spring-framework/blob/master/spring-tx/src/main/java/org/springframework/transaction/support/TransactionSynchronizationManager.java)
```java
public abstract class TransactionSynchronizationManager {

	private static final ThreadLocal<Map<Object, Object>> resources =
			new NamedThreadLocal<>("Transactional resources");

	private static final ThreadLocal<Set<TransactionSynchronization>> synchronizations =
			new NamedThreadLocal<>("Transaction synchronizations");

	private static final ThreadLocal<String> currentTransactionName =
			new NamedThreadLocal<>("Current transaction name");

	private static final ThreadLocal<Boolean> currentTransactionReadOnly =
			new NamedThreadLocal<>("Current transaction read-only status");

	private static final ThreadLocal<Integer> currentTransactionIsolationLevel =
			new NamedThreadLocal<>("Current transaction isolation level");

	private static final ThreadLocal<Boolean> actualTransactionActive =
			new NamedThreadLocal<>("Actual transaction active");
```
3. 日志框架的MDC机制，使用ThreadLocal保存线程相关的上下文信息。

# ThreadLocal源码

## ThreadLocal的get() set() setInitialValue()

从ThreadLocal读取数据，先检查ThreadLocalMap是否为空，再从map中查找。如果map为null，或者没有这个key，则执行初始化（setInitialValue）。
```java
    public T get() {
        Thread t = Thread.currentThread();
        ThreadLocalMap map = getMap(t);
        if (map != null) {
            ThreadLocalMap.Entry e = map.getEntry(this);
            if (e != null) {
                @SuppressWarnings("unchecked")
                T result = (T)e.value;
                return result;
            }
        }
        return setInitialValue();
    }
```
setInitialValue也很单，如果map为null则新建map，否则把默认值放进map。
注意`map.set(this, value)`。上面提到ThreadLocalMap的key是`ThreadLocal<?>`，这里的this正是ThreadLoca变量。
```java
    private T setInitialValue() {
        T value = initialValue();
        Thread t = Thread.currentThread();
        ThreadLocalMap map = getMap(t);
        if (map != null)
            map.set(this, value);
        else
            createMap(t, value);
        return value;
    }

```
修改的思路也是类似的。
```java
    public void set(T value) {
        Thread t = Thread.currentThread();
        ThreadLocalMap map = getMap(t);
        if (map != null)
            map.set(this, value);
        else
            createMap(t, value);
    }
```
从上面可以看到，ThreadLocal的get、set操作都交给ThreadLocalMap处理。

## ThreadLocalMap

ThreadLocal底层依靠内部类ThreadLocalMap实现。
```java
    /**
     * ThreadLocalMap is a customized hash map suitable only for
     * maintaining thread local values. No operations are exported
     * outside of the ThreadLocal class. The class is package private to
     * allow declaration of fields in class Thread.  To help deal with
     * very large and long-lived usages, the hash table entries use
     * WeakReferences for keys. However, since reference queues are not
     * used, stale entries are guaranteed to be removed only when
     * the table starts running out of space.
     */
    static class ThreadLocalMap {

        /**
         * The entries in this hash map extend WeakReference, using
         * its main ref field as the key (which is always a
         * ThreadLocal object).  Note that null keys (i.e. entry.get()
         * == null) mean that the key is no longer referenced, so the
         * entry can be expunged from table.  Such entries are referred to
         * as "stale entries" in the code that follows.
         */
        static class Entry extends WeakReference<ThreadLocal<?>> {
            /** The value associated with this ThreadLocal. */
            Object value;

            Entry(ThreadLocal<?> k, Object v) {
                super(k);
                value = v;
            }
        }
        // more code
    }
```
ThreadLocalMap的特点是，**以`ThreadLocal<?>`作为存储的key**，并且Key继承了WeakReference。

ThreadLocal本身不存储数据，真正的数据存储在Thread类。
```java
public class Thread implements Runnable {
    /* ThreadLocal values pertaining to this thread. This map is maintained
     * by the ThreadLocal class. */
    ThreadLocal.ThreadLocalMap threadLocals = null;

    /*
     * InheritableThreadLocal values pertaining to this thread. This map is
     * maintained by the InheritableThreadLocal class.
     */
    ThreadLocal.ThreadLocalMap inheritableThreadLocals = null;
```
留意Thread类和ThreadLocal类都在java.lang包下面，并且Thread类的threadLocals和inheritableThreadLocals的访问级别是default，即包级别。因此可以直接被ThreadLocal类访问。


## ThreadLocalMap.set()和replaceStaleEntry()

ThreadLocalMap是一个定制版的HashMap，专门为ThreadLocal服务。
```java
private void set(ThreadLocal<?> key, Object value) {
    // We don't use a fast path as with get() because it is at
    // least as common to use set() to create new entries as
    // it is to replace existing ones, in which case, a fast
    // path would fail more often than not.
    Entry[] tab = table;
    int len = tab.length;
    int i = key.threadLocalHashCode & (len-1);

    for (Entry e = tab[i];
         e != null;
         e = tab[i = nextIndex(i, len)]) {
        ThreadLocal<?> k = e.get();

        if (k == key) {
            e.value = value;
            return;
        }

        if (k == null) {
            replaceStaleEntry(key, value, i);
            return;
        }
    }

    tab[i] = new Entry(key, value);
    int sz = ++size;
    if (!cleanSomeSlots(i, sz) && sz >= threshold)
        rehash();
}
```
使用开链表的方式实现。真正有意思的是key为null的情况
```java
if (k == null) {
    replaceStaleEntry(key, value, i);
    return;
}
```

replaceStaleEntry寻找过时的key，并且启动清理。无论是否找到过是的key，新的value都会写入该槽位。
```java
// If we find key, then we need to swap it
// with the stale entry to maintain hash table order.
// The newly stale slot, or any other stale slot
// encountered above it, can then be sent to expungeStaleEntry
// to remove or rehash all of the other entries in run.
if (k == key) {
    e.value = value;

    tab[i] = tab[staleSlot];
    tab[staleSlot] = e;
    // Start expunge at preceding stale entry if it exists
    if (slotToExpunge == staleSlot)
        slotToExpunge = i;
    cleanSomeSlots(expungeStaleEntry(slotToExpunge), len);
    return;
}
// If we didn't find stale entry on backward scan, the
// first stale entry seen while scanning for key is the
// first still present in the run.
if (k == null && slotToExpunge == staleSlot)
    slotToExpunge = i;
```
replaceStaleEntry是为了避免内存泄露问题。

# ThreadLocal 内存泄露

ThreadLocalMap的介绍有这么一行：
>To help deal with very large and long-lived usages, the hash table entries use WeakReferences for keys. 

可见java使用WeakReference作为Entry的初衷，是为了应对ThreadLocalMap生命周期很长的情况。
由于是WeakReference，有可能出现ThreadLocal被回收了，但是底层的Entry[]数组却是强引用，最后导致value的内存无法被回收。
为了避免内存泄露，java做了如下措施：
- ThreadLocalMap.set()发现key为null，触发replaceStaleEntry()
- ThreadLocalMap.getEntry()发现key为null，触发expungeStaleEntry()
- ThreadLocalMap.remove()触发expungeStaleEntry()

expungeStaleEntry()使用rehash的方式，寻找key为null的位置，并且释放对应的value。
```java
private int expungeStaleEntry(int staleSlot) {
    Entry[] tab = table;
    int len = tab.length;
    // expunge entry at staleSlot
    tab[staleSlot].value = null;
    tab[staleSlot] = null;
    size--;
    // Rehash until we encounter null
    Entry e;
    int i;
    for (i = nextIndex(staleSlot, len);
         (e = tab[i]) != null;
         i = nextIndex(i, len)) {
        ThreadLocal<?> k = e.get();
        if (k == null) {
            e.value = null;
            tab[i] = null;
            size--;
        } else {
            int h = k.threadLocalHashCode & (len - 1);
            if (h != i) {
                tab[i] = null;
                // Unlike Knuth 6.4 Algorithm R, we must scan until
                // null because multiple entries could have been stale.
                while (tab[h] != null)
                    h = nextIndex(h, len);
                tab[h] = e;
            }
        }
    }
    return i;
}
```

# ThreadLocal和上下文

ThreadLocal可以用来保存上下文信息。
但是一个线程处理多个请求，就有可能导致这个请求读取到了上个请求遗留的上下文信息。

ThreadPoolExecutor线程池提供了入口
```java
protected void beforeExecute(Thread t, Runnable r) { }
protected void afterExecute(Runnable r, Throwable t) { }
```
可以在此执行ThreadLocal的清理操作。
 