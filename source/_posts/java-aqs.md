---
title: AbstractQueuedSynchronizer笔记
date: 2019-08-20 13:16:36
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [AbstractQueuedSynchronizer, java aqs]
description:
---

AbstractQueuedSynchronizer是JUC包的基础，解决了同步器的细节问题（同步状态、FIFO队列），ReentrantLock、Semaphore、CountDownLatch等类都使用了AQS。

# CLH lock

```
      +------+  prev +------+  prev +------+
      |      | <---- |      | <---- |      |  
 head | Node |  next | Node |  next | Node |  tail
      |      | ----> |      | ----> |      |  
      +------+       +------+       +------+
```

<!-- more -->

CLH锁通常用于自旋锁。AQS使用CLH的变种作为同步器。CLH节点数据结构如下。
```java
static final class Node {
    /** Marker to indicate a node is waiting in shared mode */
    static final Node SHARED = new Node();
    /** Marker to indicate a node is waiting in exclusive mode */
    static final Node EXCLUSIVE = null;
    
    /** waitStatus value to indicate thread has cancelled */
    static final int CANCELLED =  1;
    /** waitStatus value to indicate successor's thread needs unparking */
    static final int SIGNAL    = -1;
    /** waitStatus value to indicate thread is waiting on condition */
    static final int CONDITION = -2;
    /**
     * waitStatus value to indicate the next acquireShared should
     * unconditionally propagate
     */
    static final int PROPAGATE = -3;

    volatile int waitStatus;

    volatile Node prev;
    volatile Node next;

    /**
     * The thread that enqueued this node.  Initialized on
     * construction and nulled out after use.
     */
    volatile Thread thread;
    // 存储condition队列中的后继节点
    Node nextWaiter;
}
```

waitStatus是节点的状态。
- SIGNAL：-1。这个节点释放、或者取消的时候，要通过unpark操作通知后继节点。
- CANCELLED：1。节点由于超时或者中断，因此取消了。
- CONDITION：-2。这个节点处于条件队列。
- PROPAGATE：-3。releaseShared操作的时候要传递到其他节点。
- 0：其他。

非0数值表示这个节点不需要发送信号。
对于普通同步节点，waitStatus初始化为0，如果是条件队列节点，则初始化为CONDITION。


AQS是由CLH node构建的双向链表，head、tail分别指向链表的头部、尾部。
{% asset_img clh-lock.png %}
```java
    private transient volatile Node head;

    private transient volatile Node tail;

    /**
     * The synchronization state.
     */
    private volatile int state;
```


# AQS入队

```java
/**
 * Creates and enqueues node for current thread and given mode.
 *
 * @param mode Node.EXCLUSIVE for exclusive, Node.SHARED for shared
 * @return the new node
 */
private Node addWaiter(Node mode) {
    Node node = new Node(Thread.currentThread(), mode);
    // Try the fast path of enq; backup to full enq on failure
    Node pred = tail;
    if (pred != null) {
        node.prev = pred;
        if (compareAndSetTail(pred, node)) {
            pred.next = node;
            return node;
        }
    }
    enq(node);
    return node;
}
```
入队操作发生在tail：`node.prev = pred`。这里做了优化，假设入队竞争不大，先尝试检查和更新tail，失败才走完整的enq流程。

enq逻辑如下
```java
private Node enq(final Node node) {
    for (;;) {
        // 入队发生在tail
        Node t = tail;
        if (t == null) { // Must initialize
            // 由于AQS的head、tail节点使用了lazy init方式，
            // 所以要先检查节点是否为null，并做初始化。
            if (compareAndSetHead(new Node()))
                tail = head;
        } else {
            // 设置入队节点的前驱为之前的tail
            // 并且尝试原子化检查和更新tail
            node.prev = t;
            if (compareAndSetTail(t, node)) {
                t.next = node;
                return t;
            }
        }
    }
}

/**
 * CAS head field. Used only by enq.
 */
private final boolean compareAndSetHead(Node update) {
    return unsafe.compareAndSwapObject(this, headOffset, null, update);
}

/**
 * CAS tail field. Used only by enq.
 */
private final boolean compareAndSetTail(Node expect, Node update) {
    return unsafe.compareAndSwapObject(this, tailOffset, expect, update);
}
```
入队发生在tail在一个无限循环中不停检查和重试，直至入队成功。
底层使用了Unsafe类，直接使用底层硬件提供的原子化操作，这里先不展开。

# 获取互斥锁

```java
public final void acquire(int arg) {
    if (!tryAcquire(arg) &&
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
        selfInterrupt();
}
```
acquire是互斥方式获取锁，不支持中断。
tryAcquire是模板方法，由子类覆盖（ReentrantLock、Semaphore等）。
当尝试获取锁失败，则使用addWaiter把当前线程添加到CLH队列，并在循环中尝试。

```java
final boolean acquireQueued(final Node node, int arg) {
    boolean failed = true;
    try {
        boolean interrupted = false;
        for (;;) {
            final Node p = node.predecessor();
            // 当前节点的前驱是head，才尝试获取同步器
            // tryAcquire是模板方法，由子类覆盖
            if (p == head && tryAcquire(arg)) {
                // 更新node为head
                setHead(node);
                p.next = null; // help GC
                failed = false;
                return interrupted;
            }
            // 判断是否要阻塞线程
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}
```

有意思的是获取锁失败后，判断是否需要阻塞线程。
```java
private static boolean shouldParkAfterFailedAcquire(Node pred, Node node) {
    // 检查前驱节点的waitStatus
    int ws = pred.waitStatus;
    if (ws == Node.SIGNAL)
        // 需要被阻塞
        return true;
    if (ws > 0) {
        // ws > 0 即CANCELLED，往回找到非CANCELLED节点
        do {
            node.prev = pred = pred.prev;
        } while (pred.waitStatus > 0);
        pred.next = node;
    } else {
        /*
         * waitStatus must be 0 or PROPAGATE.  Indicate that we
         * need a signal, but don't park yet.  Caller will need to
         * retry to make sure it cannot acquire before parking.
         */
        // 其余情况设置为 SIGNAL
        compareAndSetWaitStatus(pred, ws, Node.SIGNAL);
    }
    return false;
}

private final boolean parkAndCheckInterrupt() {
    // 使用LockSupport阻塞当前线程
    LockSupport.park(this);
    return Thread.interrupted();
}
```


# 释放互斥锁

```java
public final boolean release(int arg) {
    // tryRelease是模板方法，由子类覆盖
    if (tryRelease(arg)) {
        // 在head释放锁
        Node h = head;
        if (h != null && h.waitStatus != 0)
            unparkSuccessor(h);
        return true;
    }
    return false;
}

private void unparkSuccessor(Node node) {
    /*
     * If status is negative (i.e., possibly needing signal) try
     * to clear in anticipation of signalling.  It is OK if this
     * fails or if status is changed by waiting thread.
     */
    int ws = node.waitStatus;
    if (ws < 0)
        compareAndSetWaitStatus(node, ws, 0);
    /*
     * Thread to unpark is held in successor, which is normally
     * just the next node.  But if cancelled or apparently null,
     * traverse backwards from tail to find the actual
     * non-cancelled successor.
     */
    Node s = node.next;
    // 没有后继节点，或者已经CANCELLED
    // 则需要从tail往回遍历，寻找当前节点的后继
    if (s == null || s.waitStatus > 0) {
        s = null;
        for (Node t = tail; t != null && t != node; t = t.prev)
            if (t.waitStatus <= 0)
                s = t;
    }
    if (s != null)
        LockSupport.unpark(s.thread);
}
```

# 获取共享锁

```java
public final void acquireShared(int arg) {
    // tryAcquireShared是模板方法
    if (tryAcquireShared(arg) < 0)
        doAcquireShared(arg);
}

private void doAcquireShared(int arg) {
    final Node node = addWaiter(Node.SHARED);
    boolean failed = true;
    try {
        boolean interrupted = false;
        for (;;) {
            final Node p = node.predecessor();
            // 前驱是head，才尝试获取锁
            if (p == head) {
                int r = tryAcquireShared(arg);
                if (r >= 0) {
                    setHeadAndPropagate(node, r);
                    p.next = null; // help GC
                    if (interrupted)
                        selfInterrupt();
                    failed = false;
                    return;
                }
            }
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}
```

因为是shared模式，获取锁之后，可能要通知后面的节点
```java
/**
 * Sets head of queue, and checks if successor may be waiting
 * in shared mode, if so propagating if either propagate > 0 or
 * PROPAGATE status was set.
 *
 * @param node the node
 * @param propagate the return value from a tryAcquireShared
 */
private void setHeadAndPropagate(Node node, int propagate) {
    Node h = head; // Record old head for check below
    setHead(node);
    /*
     * Try to signal next queued node if:
     *   Propagation was indicated by caller,
     *     or was recorded (as h.waitStatus either before
     *     or after setHead) by a previous operation
     *     (note: this uses sign-check of waitStatus because
     *      PROPAGATE status may transition to SIGNAL.)
     * and
     *   The next node is waiting in shared mode,
     *     or we don't know, because it appears null
     *
     * The conservatism in both of these checks may cause
     * unnecessary wake-ups, but only when there are multiple
     * racing acquires/releases, so most need signals now or soon
     * anyway.
     */
    // propagate > 0：还有剩余，需要传递
    // h.waitStatus < 0 ：SIGNAL or PROPAGATE
    if (propagate > 0 || h == null || h.waitStatus < 0 ||
        (h = head) == null || h.waitStatus < 0) {
        Node s = node.next;
        if (s == null || s.isShared())
            doReleaseShared();
    }
}
```


# 释放共享锁

```java
public final boolean releaseShared(int arg) {
    // tryReleaseShared是模板方法
    if (tryReleaseShared(arg)) {
        doReleaseShared();
        return true;
    }
    return false;
}
```

```java
private void doReleaseShared() {
    /*
     * Ensure that a release propagates, even if there are other
     * in-progress acquires/releases.  This proceeds in the usual
     * way of trying to unparkSuccessor of head if it needs
     * signal. But if it does not, status is set to PROPAGATE to
     * ensure that upon release, propagation continues.
     * Additionally, we must loop in case a new node is added
     * while we are doing this. Also, unlike other uses of
     * unparkSuccessor, we need to know if CAS to reset status
     * fails, if so rechecking.
     */
    for (;;) {
        // 在head释放锁
        Node h = head;
        if (h != null && h != tail) {
            int ws = h.waitStatus;
            // SIGNAL需要唤醒后续节点
            if (ws == Node.SIGNAL) {
                if (!compareAndSetWaitStatus(h, Node.SIGNAL, 0))
                    continue;            // loop to recheck cases
                unparkSuccessor(h);
            }
            // why 转为 PROPAGATE 状态？
            else if (ws == 0 &&
                     !compareAndSetWaitStatus(h, 0, Node.PROPAGATE))
                continue;                // loop on failed CAS
        }
        if (h == head)                   // loop if head changed
            break;
    }
}
```

# Node.PROPAGATE

AQS源码比较难理解的是Node.PROPAGATE。javadoc对Node.PROPAGATE的解释
```
PROPAGATE:  A releaseShared should be propagated to other
            nodes. This is set (for head node only) in
            doReleaseShared to ensure propagation
            continues, even if other operations have
            since intervened.
```
在共享模式下，可以认为资源有多个，因此当前线程被唤醒之后，可能还有剩余的资源可以唤醒其他线程。**该状态用来表明后续节点会传播唤醒的操作。需要注意的是只有头节点才可以设置为该状态**

找到一篇文章，对此思考比较深入，推荐阅读：[AbstractQueuedSynchronizer源码解读](https://www.cnblogs.com/micrari/p/6937995.html)

>在AQS的共享锁中，一个被park的线程，不考虑线程中断和前驱节点取消的情况，有两种情况可以被unpark：一种是其他线程释放信号量，调用unparkSuccessor；另一种是其他线程获取共享锁时通过传播机制来唤醒后继节点。
>可能会有队列中处于等待状态的节点因为第一个线程完成释放唤醒，第二个线程获取到锁，但还没设置好head，又有新线程释放锁，但是读到老的head状态为0导致释放但不唤醒，最终后一个等待线程既没有被释放线程唤醒，也没有被持锁线程唤醒。
>PROPAGATE的引入是为了解决共享锁并发释放导致的线程hang住问题。

setHeadAndPropagate()
```java
if (propagate > 0 || h == null || h.waitStatus < 0 ||
    (h = head) == null || h.waitStatus < 0) {
    Node s = node.next;
    if (s == null || s.isShared())
        doReleaseShared();
}
```

doReleaseShared()
```java
else if (ws == 0 &&
         !compareAndSetWaitStatus(h, 0, Node.PROPAGATE))
    continue;                // loop on failed CAS
```

# 小结

- AQS使用CLH节点，构建双向链表
- AQS提供了模板方法（tryXXX，例如tryRelease、tryAcquire），由子类覆盖
- AQS支持互斥锁、共享锁、条件队列
- 在tail增加等待线程
- 在head获取锁、释放锁
- 使用unsafe类CAS更新head、tail
- 释放锁且Node.SIGNAL，则要通过unparkSuccessor唤醒后续节点
- 对于共享锁，为了解决并发释放导致线程hang的情况，增加了Node.PROPAGATE。
- 只有head节点才可以设置为PROPAGATE状态

# 参考

- [【Java并发】详解 AbstractQueuedSynchronizer](http://blog.zhangjikai.com/2017/04/15/%E3%80%90Java-%E5%B9%B6%E5%8F%91%E3%80%91%E8%AF%A6%E8%A7%A3-AbstractQueuedSynchronizer/)
- [AbstractQueuedSynchronizer源码解读](https://www.cnblogs.com/micrari/p/6937995.html)