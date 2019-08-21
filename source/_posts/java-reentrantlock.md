---
title: Java ReentrantLock原理
date: 2019-08-21 11:12:31
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [ReentrantLock 源码, ReentrantLock vs synchronized]
description: ReentrantLock支持公平、非公平方式获取互斥锁锁。是可重入锁。使用AQS的state字段记录获取锁的次数。
---

有了AQS的基础，可以了解ReentrantLock的原理。
相关文章
- {% post_link java-aqs %}

# ReentrantLock简介

ReentrantLock支持公平、非公平方式获取互斥锁锁。

- 公平锁（Fair）：加锁前检查是否有排队等待的线程，优先排队等待的线程，先来先得 
- 非公平锁（NonFair）：加锁时不考虑排队等待问题，直接尝试获取锁，获取不到自动到队尾等待

ReentrantLock正如其名，是可重入的
>可重入锁，也叫做递归锁，指的是同一线程 外层函数获得锁之后 ，内层递归函数仍然有获取该锁的代码，但不受影响。

ReentrantLock底层使用了AQS工具类。ReentrantLock和AQS的关系如下：
{% asset_img reentrantlock.png %}

ReentrantLock的内部类Sync继承自AQS，还有FairSync、NonFairSync继承于Sync类。

<!-- more -->

# ReentrantLock源码

ReentrantLock内部包含一个Sync实例，核心的lock、unlock操作交给Sync实例负责。
Sync实例可以是NonFairSync或者FairSync。
```java
public class ReentrantLock implements Lock, java.io.Serializable {
    /** Synchronizer providing all implementation mechanics */
    private final Sync sync;

    public void lock() {
        sync.lock();
    }

    public void unlock() {
        sync.release(1);
    }
```

## ReentranLock.Sync

AbstractQueuedSynchronizer提供了tryXXX模板方法，供子类覆盖。Sync覆盖了tryRelease()，并且提供了nonfairTryAcquire()
```java
abstract static class Sync extends AbstractQueuedSynchronizer {

    abstract void lock();

    /**
     * Performs non-fair tryLock.  tryAcquire is implemented in
     * subclasses, but both need nonfair try for trylock method.
     */
    final boolean nonfairTryAcquire(int acquires) {
        final Thread current = Thread.currentThread();
        int c = getState();
        if (c == 0) {
            // 使用AQS.state字段保存
            // 对于非公平锁，一旦发现锁可以占有，则当前线程抢占锁
            if (compareAndSetState(0, acquires)) {
                setExclusiveOwnerThread(current);
                return true;
            }
        }
        else if (current == getExclusiveOwnerThread()) {
            // 可重入锁，更新当前获取的许可数
            int nextc = c + acquires;
            if (nextc < 0) // overflow
                throw new Error("Maximum lock count exceeded");
            setState(nextc);
            return true;
        }
        return false;
    }

    protected final boolean tryRelease(int releases) {
        int c = getState() - releases;
        // 检擦当前线程是否拥有互斥锁
        if (Thread.currentThread() != getExclusiveOwnerThread())
            throw new IllegalMonitorStateException();
        boolean free = false;
        // 因为是可重入，一个线程可以多次获取锁
        if (c == 0) {
            free = true;
            setExclusiveOwnerThread(null);
        }
        setState(c);
        return free;
    }
```
回想AQS的属性
```java
private transient volatile Node head;
private transient volatile Node tail;
/**
 * The synchronization state.
 */
private volatile int state;
```
子类使用state字段存储同步状态。这里使用state记录线程获取锁的次数。

ReentranLock是互斥锁，每次获取的许可数都是1。释放锁则可以一次释放多个许可。

## NonfairSync
```java
static final class NonfairSync extends Sync {

    final void lock() {
        // fast-path
        if (compareAndSetState(0, 1))
            setExclusiveOwnerThread(Thread.currentThread());
        else
            acquire(1);
    }

    protected final boolean tryAcquire(int acquires) {
        return nonfairTryAcquire(acquires);
    }
}
```

## FairSync

```java
static final class FairSync extends Sync {
    final void lock() {
        acquire(1);
    }

    /**
     * Fair version of tryAcquire.  Don't grant access unless
     * recursive call or no waiters or is first.
     */
    protected final boolean tryAcquire(int acquires) {
        final Thread current = Thread.currentThread();
        int c = getState();
        if (c == 0) {
            // 公平锁，在抢占锁之前，先检查有无等待的前驱节点
            if (!hasQueuedPredecessors() &&
                compareAndSetState(0, acquires)) {
                setExclusiveOwnerThread(current);
                return true;
            }
        }
        else if (current == getExclusiveOwnerThread()) {
            int nextc = c + acquires;
            if (nextc < 0)
                throw new Error("Maximum lock count exceeded");
            setState(nextc);
            return true;
        }
        return false;
    }
}
```

# ReentrantLock实践

一定要释放锁。通常在finally释放。
```java
ReentrantLock lock=new ReentrantLock();
try{
    lock.tryLock();
    // do something
}finally{
    lock.unlock();
}
```

# 公平锁 vs 非公平锁

公平锁按照请求资源的先后顺序获取锁。会导致频繁切换线程上下文。吞吐量比非公平锁低。
非公平锁获取锁的时候不会检查等待队列。可能发生一个线程反复获取锁，导致其他线程发生“饥饿”。

# ReentrantLock vs synchronized

ReentrantLock支持公平锁、非公平锁模式，synchronized是非公平锁。
ReentrantLock和synchronized都是可重入锁。
ReentrantLock底层使用AQS实现，synchronized使用java的隐式锁实现。
ReentrantLock支持超时等待（tryLock）。
在java6之前，synchronized性能要比ReentrantLock低。

# ReentrantLock和Condition

Condition是线程间通信的方式。Condition要绑定Lock。ReentrantLock提供了Condition支持。具体参见
- {% post_link java-condition %}

# 小结

ReentrantLock使用了AQS的互斥锁能力。使用state变量记录线程获取锁的次数。

