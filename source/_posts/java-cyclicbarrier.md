---
title: Java CyclicBarrier原理
date: 2019-08-22 11:18:42
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [cyclicbarrier 源码, cyclicbarrier 详解, cyclicbarrier vs countdownlatch]
description: CyclicBrrier能够让一组线程，直到所有线程到达屏障。CyclicBarrier可以反复使用。
---

# CyclicBrrier

CyclicBrrier是一个有趣的工具，能够让一组线程阻塞等待彼此
>allows a set of threads to all wait for each other to reach a common barrier point.

Cyclic的意思是“循环”，即CyclicBrrier可以使用多此。
（ps. 之前提到CountDownLatch也可以使一组线程阻塞等待，但是CountDownLatch只能使用一次。）

{% asset_img v1_cyclicbarrier.png cyclicbarrier %}
(图片来源：`https://www.geeksforgeeks.org/java-util-concurrent-cyclicbarrier-java/`)

<!-- more -->

# CyclicBrrier 例子

```java
public class TestCyclicBarrier {

    public static void main(String[] args) {
        ExecutorService es = Executors.newCachedThreadPool();
        final int PLAYER_COUNT = 5;
        CyclicBarrier barrier = new CyclicBarrier(PLAYER_COUNT, () -> System.out.println("bang!"));
        for (int i = 0; i < PLAYER_COUNT; i++) {
            int pid = i;
            es.submit(() -> {
                try {
                    System.out.println("player[" + pid + "] is ready");
                    barrier.await();
                    System.out.println("player[" + pid + "] is done");
                } catch (InterruptedException e) {
                    e.printStackTrace();
                } catch (BrokenBarrierException e) {
                    e.printStackTrace();
                }
            });
        }
        es.shutdown();
    }
```
输出
```
player[0] is ready
player[4] is ready
player[1] is ready
player[3] is ready
player[2] is ready
bang!
player[2] is done
player[1] is done
player[3] is done
player[4] is done
player[0] is done
```

1. 初始化CyclicBarrier
```java
public CyclicBarrier(int parties)
public CyclicBarrier(int parties, Runnable barrierAction)
```
- parties：需要多少个线程到达屏障
- barrierAction：可选，到达屏障触发一个动作

2. 每个线程执行`barrier.await()`，表示到达屏障并且等待。

# CyclicBrrier 源码

从上面来看，入口是CyclicBrrier.await()方法。不过在深入之前，先了解下CyclicBrrier的结构。
```java
private static class Generation {
    boolean broken = false;
}

/** The lock for guarding barrier entry */
private final ReentrantLock lock = new ReentrantLock();
/** Condition to wait on until tripped */
private final Condition trip = lock.newCondition();
/** The number of parties */
private final int parties;
/* The command to run when tripped */
private final Runnable barrierCommand;
/** The current generation */
private Generation generation = new Generation();

/**
 * Number of parties still waiting. Counts down from parties to 0
 * on each generation.  It is reset to parties on each new
 * generation or when broken.
 */
private int count;
```
CyclicBrrier有个内部类Generation。之前提到CyclicBrrier可以反复使用：每次复用CyclicBrrier，generation就会reset。
为了屏障的安全性，使用了ReentrantLock保护。从后面的代码看出，需要保护的操作是，更新剩余等待线程数，即count变量。
ReentrantLock上绑定了一个等待队列trip。所有进入屏障等待的线程，都会进入trip等待队列。

回到await()方法，实际调用的是dowait()

1. 检查generation合法性
2. 如果发生了中断，则这个屏障已经坏掉，唤醒所有等待的线程
```java
/**
 * Sets current barrier generation as broken and wakes up everyone.
 * Called only while holding lock.
 */
private void breakBarrier() {
    generation.broken = true;
    count = parties;
    trip.signalAll();
}
```
3. 如果最后一个线程进入了屏障，则执行barrierCommand。nextGeneration会唤醒所有线程，同时更新generation实例。每次复位CyclicBrrier，即生成新的Generation。
```java
int index = --count;
if (index == 0) {  // tripped
    boolean ranAction = false;
    try {
        final Runnable command = barrierCommand;
        if (command != null)
            command.run();
        ranAction = true;
        nextGeneration();
        return 0;
    } finally {
        if (!ranAction)
            breakBarrier();
    }
}

private void nextGeneration() {
    // signal completion of last generation
    trip.signalAll();
    // set up next generation
    count = parties;
    generation = new Generation();
}
```

4. 加入trip条件队列等待，或者发生超时、屏障坏掉、中断等异常而退出
```java
// loop until tripped, broken, interrupted, or timed out
for (;;) {
    try {
        if (!timed)
            trip.await();
        else if (nanos > 0L)
            nanos = trip.awaitNanos(nanos);
    } catch (InterruptedException ie) {
        if (g == generation && ! g.broken) {
            breakBarrier();
            throw ie;
        } else {
            // We're about to finish waiting even if we had not
            // been interrupted, so this interrupt is deemed to
            // "belong" to subsequent execution.
            Thread.currentThread().interrupt();
        }
    }
    if (g.broken)
        throw new BrokenBarrierException();
    if (g != generation)
        return index;
    if (timed && nanos <= 0L) {
        breakBarrier();
        throw new TimeoutException();
    }
}
```

5. 最后在finally释放ReentrantLock

# CyclicBrrier vs CountDownLatch

CyclicBrrier设计了generation字段，因此可以重复使用，通过nextGeneration()重置屏障。CountDownLatch只能使用一次。
CyclicBrrier支持在唤醒线程之前，执行自定义的命令（barrierCommand）。CountDownLatch不支持。

# 小结

- CyclicBrrier使用ReentrantLock保护屏障
- 在屏障处更新count（剩余等待线程计数）
- 所有等待线程都会加入trip条件队列，并且阻塞
- 等count==0，唤醒所有等待的线程

