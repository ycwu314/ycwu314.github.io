---
title: Java CountDownLatch原理
date: 2019-08-21 20:21:30
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [CountDownLatch 源码, CountDownLatch 例子]
description: CountDownLatch使用AQS的state字段存储计数。CountDownLatch只能使用一次，没有复位操作
---

# CountDownLatch

CountDownLatch，字面上是倒计数的门闩，也就是倒计数结束的时候，开门干事情。javadoc介绍很清楚
>A synchronization aid that allows one or more threads to wait until a set of operations being performed in other threads completes.

CountDownLatch可以让一组线程阻塞，直到收到唤醒。
CountDownLatch底层使用AQS实现。相关文章见：
- {% post_link java-aqs %}

# CountDownLatch 源码分析

{% asset_img CountDownLatch.png CountDownLatch %}

<!-- more -->

回忆AQS的节点：
```java
private transient volatile Node head;
private transient volatile Node tail;

/**
 * The synchronization state.
 */
private volatile int state;
```
子类使用state字段存储同步状态。

CountDownLatch使用AQS.state字段存储可用的计数。
```java
    private static final class Sync extends AbstractQueuedSynchronizer {
        private static final long serialVersionUID = 4982264981922014374L;

        Sync(int count) {
            setState(count);
        }

        int getCount() {
            return getState();
        }
    }
```
留意state只有在初始化的时候可以设置。也就是说，**CountDownLatch只能使用一次，没有复位操作**。

## CountDownLatch.await()

CountDownLatch.await()
```java
public void await() throws InterruptedException {
    sync.acquireSharedInterruptibly(1);
}
```
调用AQS的acquireSharedInterruptibly
```java
    public final void acquireSharedInterruptibly(int arg)
            throws InterruptedException {
        if (Thread.interrupted())
            throw new InterruptedException();
        // tryAcquireShared是模板方法，由子类覆盖
        if (tryAcquireShared(arg) < 0)
            doAcquireSharedInterruptibly(arg);
    }
```
最终使用Sync.tryAcquireShared
```java
protected int tryAcquireShared(int acquires) {
    return (getState() == 0) ? 1 : -1;
}
```
只要计数≠0，就使用AQS.doAcquireSharedInterruptibly()阻塞等待
```java
private void doAcquireSharedInterruptibly(int arg)
    throws InterruptedException {
    final Node node = addWaiter(Node.SHARED);
    boolean failed = true;
    try {
        for (;;) {
            final Node p = node.predecessor();
            if (p == head) {
                int r = tryAcquireShared(arg);
                if (r >= 0) {
                    setHeadAndPropagate(node, r);
                    p.next = null; // help GC
                    failed = false;
                    return;
                }
            }
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                throw new InterruptedException();
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}
```

## CountDownLatch.countDown()

CountDownLatch.countDown()减少计数，实际是释放共享锁
```java
/**
* Decrements the count of the latch, releasing all waiting threads if the count reaches zero.
* If the current count is greater than zero then it is decremented. If the new count is zero then all waiting threads are re-enabled for thread scheduling purposes.
* If the current count equals zero then nothing happens.
**/
public void countDown() {
    sync.releaseShared(1);
}
```
使用了AQS.releaseShared()
```java
    public final boolean releaseShared(int arg) {
        // tryReleaseShared是模板方法，由子类覆盖
        if (tryReleaseShared(arg)) {
            doReleaseShared();
            return true;
        }
        return false;
    }
```
最终使用Sync.tryReleaseShared
```java
protected boolean tryReleaseShared(int releases) {
    // Decrement count; signal when transition to zero
    for (;;) {
        int c = getState();
        // 计数为0，则返回false，由AQS.doReleaseShared()唤醒所有等待的线程
        if (c == 0)
            return false;
        int nextc = c-1;
        // CAS更新
        if (compareAndSetState(c, nextc))
            return nextc == 0;
    }
}
```
当state==0，唤醒所有等待的线程
```java
private void doReleaseShared() {
    for (;;) {
        Node h = head;
        if (h != null && h != tail) {
            int ws = h.waitStatus;
            if (ws == Node.SIGNAL) {
                if (!compareAndSetWaitStatus(h, Node.SIGNAL, 0))
                    continue;            // loop to recheck cases
                // 唤醒线程    
                unparkSuccessor(h);
            }
            else if (ws == 0 &&
                     !compareAndSetWaitStatus(h, 0, Node.PROPAGATE))
                continue;                // loop on failed CAS
        }
        if (h == head)                   // loop if head changed
            break;
    }
}
```

# CountDownLatch 例子

```java
public class TestCountDownLatch {

    public static void main(String[] args) {
        final int SIZE = 5;
        AtomicInteger ready = new AtomicInteger(0);
        CountDownLatch latch = new CountDownLatch(1);
        for (int i = 0; i < SIZE; i++) {
            int pid = i;
            new Thread(() -> {
                try {
                    System.out.println("thread[" + pid + "] is ready");
                    ready.incrementAndGet();
                    latch.await();
                    System.out.println("thread[" + pid + "] done.");

                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }).start();
        }
        // spin
        while (ready.get() < SIZE) {

        }
        latch.countDown();

    }
}
```
在性能测试里，可以使用CountDownLatch模拟多线程瞬间并发。


# 小结

- CountDownLatch内部类Sync继承了AQS
- CountDownLatch使用AQS.state保存计数。countDown()减少计数。当计数==0，唤醒所有等待的线程
- CountDownLatch只能使用一次，不能复位
