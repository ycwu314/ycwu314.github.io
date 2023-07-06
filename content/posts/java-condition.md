---
title: Condition原理，以及实现生产者消费者模式
date: 2019-08-21 15:08:35
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [condition 源码, condition 原理, condition 生产者 消费者, ConditionObject, 线程间通信]
description: Condition接口实现线程间通信。底层使用AQS的ConditionObject
---

# Condition简介

java线程间通信，除了可以使用Object提供的wait/notify/notifyAll之外，还可以使用java.util.concurrent.locks.Condition接口。Condition接口的await/signal/signalAll分别对应Object的wait/notify/notifyAll。
相比Object提供的线程间通信机制，Condition接口支持在一个对象上创建多个等待队列（having multiple wait-sets per object）；而Object机制使用隐式锁，只有一个等待队列。
Condition实例和一个Lock对象绑定。因此在使用Condition实例方法之前，要先获得Lock。

|  | Object | Condition |
|--------------|--------------|-------------|
| 使用方式 | synchronized | lock.newCondition(); <br> lock.lock() |
| 等待队列数量 | 1个 | 多个 |
| 支持超时等待 | no | yes |
| 支持中断 | no | yes |

<!-- more -->

# 使用Condition实现生产者消费者模式

```java
public class TestCondition {

    private int MAX_SIZE = 10;
    private ReentrantLock lock = new ReentrantLock();
    // having multiple wait-sets per object
    private Condition notFull = lock.newCondition();
    private Condition notEmpty = lock.newCondition();
    private LinkedList<Integer> holders = new LinkedList<>();

    @Test
    public void test() {
        new Thread(new Producer()).start();
        new Thread(new Consumer()).start();
        try {
            Thread.currentThread().join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    class Consumer implements Runnable {

        @Override
        public void run() {
            while (true) {
                try {
                    lock.lock();
                    while (holders.isEmpty()) {
                        notEmpty.await();
                    }

                    int x = holders.removeFirst();
                    System.out.println("consumes: " + x);
                    notFull.signal();
                    Thread.sleep(500);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                } finally {
                    lock.unlock();
                }
            }
        }
    }

    class Producer implements Runnable {

        @Override
        public void run() {
            Random random = new Random();
            while (true) {
                try {
                    lock.lock();
                    // 在循环中检查条件，处理虚假唤醒的情况
                    while (holders.size() == MAX_SIZE) {
                        notFull.await();
                    }

                    int x = random.nextInt(100);
                    holders.addLast(x);
                    System.out.println("produce: " + x);

                    notEmpty.signal();
                    Thread.sleep(500);

                } catch (InterruptedException e) {
                    e.printStackTrace();
                } finally {
                    lock.unlock();
                }
            }
        }
    }
}
```

# Condition相关源码

Condition要与Lock对象绑定。以ReentrantLock为例，
```java
public class ReentrantLock implements Lock, java.io.Serializable{

    abstract static class Sync extends AbstractQueuedSynchronizer {
        final ConditionObject newCondition() {
            return new ConditionObject();
        }
    }
}
```
实际使用的AQS.ConditionObject类。
ConditionObject使用CLH node构建双向链表，是FIFO队列。
```java
public class ConditionObject implements Condition, java.io.Serializable {
    private static final long serialVersionUID = 1173984872572414699L;
    /** First node of condition queue. */
    private transient Node firstWaiter;
    /** Last node of condition queue. */
    private transient Node lastWaiter;
```

## addConditionWaiter

添加等待线程的操作发生在lastWaiter（链表尾部）。注意Condition类型的等待队列，节点的waitStatus是Node.CONDITION。
```java
/**
 * Adds a new waiter to wait queue.
 * @return its new wait node
 */
private Node addConditionWaiter() {
    Node t = lastWaiter;
    // If lastWaiter is cancelled, clean out.
    if (t != null && t.waitStatus != Node.CONDITION) {
        unlinkCancelledWaiters();
        t = lastWaiter;
    }
    Node node = new Node(Thread.currentThread(), Node.CONDITION);
    if (t == null)
        firstWaiter = node;
    else
        t.nextWaiter = node;
    lastWaiter = node;
    return node;
}
```
因为等待队列中的节点可能取消等待，因此要从头开始检查。触发unlinkCancelledWaiters的时机有2个：
- 等待队列的lastWaiter已经取消
- 发送await，这时候已经获取了锁
```java
private void unlinkCancelledWaiters() {
    Node t = firstWaiter;
    Node trail = null;
    while (t != null) {
        Node next = t.nextWaiter;
        // 因为是条件队列，waitStatus != Node.CONDITION 都认为是取消等待。
        if (t.waitStatus != Node.CONDITION) {
            t.nextWaiter = null;
            if (trail == null)
                firstWaiter = next;
            else
                trail.nextWaiter = next;
            if (next == null)
                lastWaiter = trail;
        }
        else
            trail = t;
        t = next;
    }
}
```

## signal

从链表头部开始遍历，唤醒一个节点
```java
public final void signal() {
    if (!isHeldExclusively())
        throw new IllegalMonitorStateException();
    Node first = firstWaiter;
    if (first != null)
        doSignal(first);
}

private void doSignal(Node first) {
    do {
        if ( (firstWaiter = first.nextWaiter) == null)
            lastWaiter = null;
        first.nextWaiter = null;
    } while (!transferForSignal(first) &&
             (first = firstWaiter) != null);
}
```

transferForSignal方法，把条件队列的节点丢到同步队列，这样线程被“唤醒”，可以参与竞争锁
```java
/**
* Transfers a node from a condition queue onto sync queue.
*/
final boolean transferForSignal(Node node) {
    /*
     * If cannot change waitStatus, the node has been cancelled.
     */
    if (!compareAndSetWaitStatus(node, Node.CONDITION, 0))
        return false;

    /*
     * Splice onto queue and try to set waitStatus of predecessor to
     * indicate that thread is (probably) waiting. If cancelled or
     * attempt to set waitStatus fails, wake up to resync (in which
     * case the waitStatus can be transiently and harmlessly wrong).
     */
    // 把节点插入到AQS同步队列的tail，这样线程可以参与竞争锁
    // 并且返回它的前驱
    Node p = enq(node);
    int ws = p.waitStatus;
    // 当前前驱的ws为SIGNAL，才需要唤醒后面的节点。
    if (ws > 0 || !compareAndSetWaitStatus(p, ws, Node.SIGNAL))
        LockSupport.unpark(node.thread);
    return true;
}
```

signalAll也是类似的思路，在此不重复。


## await

Condition的await对应Object的wait，因此等待的时候会释放lock。
```java
public final void await() throws InterruptedException {
    if (Thread.interrupted())
        throw new InterruptedException();
    
    // 释放锁后要再次等待锁，因此加入到Condition等待队列
    Node node = addConditionWaiter();
    // 释放锁
    int savedState = fullyRelease(node);
    int interruptMode = 0;
    // 自旋检查并且阻塞，直到进入sync队列，或者被中断
    while (!isOnSyncQueue(node)) {
        LockSupport.park(this);
        if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
            break;
    }
    // 获取锁
    if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
        interruptMode = REINTERRUPT;
    if (node.nextWaiter != null) // clean up if cancelled
        unlinkCancelledWaiters();
    if (interruptMode != 0)
        reportInterruptAfterWait(interruptMode);
}
```

```java
final int fullyRelease(Node node) {
    boolean failed = true;
    try {
        // 获取AQS的state字段，保存的是同步状态
        int savedState = getState();
        // release会调用模板方法tryRelease
        if (release(savedState)) {
            failed = false;
            return savedState;
        } else {
            throw new IllegalMonitorStateException();
        }
    } finally {
        if (failed)
            node.waitStatus = Node.CANCELLED;
    }
}
```
回忆：AQS的state字段用来保存同步状态。在ReentrantLock实现中，state字段用来记录当前lock被获取了几次。

isOnSyncQueue检查刚放进condition队列的节点，是否在sync队列。isOnSyncQueue方法做的检查比较多
```java
/**
 * Returns true if a node, always one that was initially placed on
 * a condition queue, is now waiting to reacquire on sync queue.
 * @param node the node
 * @return true if is reacquiring
 */
final boolean isOnSyncQueue(Node node) {
    // CONDITION表明在condition队列
    // node.prev == null : 进入sync队列，是在tail入队，且node.prev设置为之前的tail
    //     因此null表明肯定没有进入队列
    if (node.waitStatus == Node.CONDITION || node.prev == null)
        return false;
    // 进入sync队列，则在tail入队，node.next被设置为null
    // 因此next != null 肯定已经在sync队列
    if (node.next != null) // If has successor, it must be on queue
        return true;
    /*
     * node.prev can be non-null, but not yet on queue because
     * the CAS to place it on queue can fail. So we have to
     * traverse from tail to make sure it actually made it.  It
     * will always be near the tail in calls to this method, and
     * unless the CAS failed (which is unlikely), it will be
     * there, so we hardly ever traverse much.
     */

    // 这时候node.next==null & node.prev!=null
    // 可以认为node正处于放入Sync队列的执行CAS操作执行过程中。而这个CAS操作有可能失败
    // 遍历sync队列检查 
    return findNodeFromTail(node);
}

/**
 * Returns true if node is on sync queue by searching backwards from tail.
 * Called only when needed by isOnSyncQueue.
 * @return true if present
 */
private boolean findNodeFromTail(Node node) {
    Node t = tail;
    for (;;) {
        if (t == node)
            return true;
        if (t == null)
            return false;
        t = t.prev;
    }
}
```

# 小结

- await()唤醒Condition队列中第一个Node
- signal就是唤醒Condition队列中的第一个非CANCELLED节点线程，而signalAll就是唤醒所有非CANCELLED节点线程。遇到CANCELLED线程就需要将其从FIFO队列中剔除。

# 参考

- [Java多线程之JUC包：Condition源码学习笔记](https://www.cnblogs.com/go2sea/p/5630355.html)
- [Java多线程（九）之ReentrantLock与Condition](https://blog.csdn.net/vernonzheng/article/details/8288251)
