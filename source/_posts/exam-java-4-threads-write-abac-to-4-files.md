---
title: 四个线程循环输出ABCD
date: 2019-08-24 18:44:16
tags: [java]
categories: [java]
keywords: [线程间通讯]
description: 线程间通信。可以使用Object的wait、notify。也可以使用Condition的await、signal。
---

# 题目

>四个线程A、B、C、D向四个文件写入数据。要求A线程只写入A，B线程只写入B……
最终达到的效果：
A.txt内容为： A    B    C    D    A    B    C    D……
B.txt内容为： B    C    D    A    B    C    D    A……
C.txt内容为： C    D    A    B    C    D    A    B……
D:txt内容为： D    A    B    C    D    A    B    C……

<!-- more -->

# 分析

每个线程的职责：A线程只写A，B线程只写B，etc。

使用一个锁，保护共享资源即可。

怎样使4个线程按顺序写入？
很简单，一开始4个线程都处于阻塞状态，然后先唤醒A。这样A结束后，自动唤醒B，etc。
本质是**线程间通信**。可以使用Object的wait、notfiy，也可以使用Condition的await、signal。具体可以看看：
- {% post_link java-condition %}
- {% post_link java-wait-notify %}

怎样控制结束？假设执行X次后自动结束。增加一个变量X，到达指定次数后结束。
但是有个细节点，后面的线程阻塞了，依赖前面的线程唤醒，才能结束。**因此前一个线程结束的时候，要唤醒下一个线程**。

```java
public class PrintABCDBySequence {

    // 执行次数
    static final int RUN_COUNT = 10;
    static volatile boolean stop = false;
    static volatile boolean hasInit = false;
    static AtomicInteger round = new AtomicInteger();
    static int size = 4;
    // 模拟向size个文件输出
    static List<String>[] output = new ArrayList[size];
    // 等待size个线程结束
    static CountDownLatch latch = new CountDownLatch(size);

    static ReentrantLock lock = new ReentrantLock();
    static Condition waitForA = lock.newCondition();
    static Condition waitForB = lock.newCondition();
    static Condition waitForC = lock.newCondition();
    static Condition waitForD = lock.newCondition();

    public static void main(String[] args) throws InterruptedException {

        for (int i = 0; i < size; i++) {
            output[i] = new ArrayList<>();
        }

        new Thread(new PrintTask("A", waitForD, waitForA)).start();
        new Thread(new PrintTask("B", waitForA, waitForB)).start();
        new Thread(new PrintTask("C", waitForB, waitForC)).start();
        new Thread(new PrintTask("D", waitForC, waitForD)).start();

        // 等待4个线程启动
        Thread.sleep(500);
        hasInit = true;
        lock.lock();
        // 先唤醒A
        try {
            waitForD.signal();
        } finally {
            lock.unlock();
        }

        latch.await();

        for (List<String> a : output) {
            System.out.println(a);
        }
    }

    static class PrintTask implements Runnable {

        private String ch;
        private Condition prevCondition;
        private Condition selfCondition;

        public PrintTask(String ch, Condition prevCondition, Condition selfCondition) {
            this.ch = ch;
            this.prevCondition = prevCondition;
            this.selfCondition = selfCondition;
        }

        @Override
        public void run() {

            while (true) {
                lock.lock();
                // 初始化，线程进入阻塞等待
                if (!hasInit) {
                    try {
                        prevCondition.await();
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }

                try {
                    // attention: stop的时候，要先唤醒后面的线程，否则后面的线程不能结束
                    if (stop) {
                        selfCondition.signal();
                        break;
                    }

                    int r = round.getAndIncrement();
                    for (int i = 0; i < output.length; i++) {
                        if (i <= r) {
                            output[i].add(ch);
                        } else {
                            break;
                        }
                    }

                    if (r >= RUN_COUNT) {
                        stop = true;
                    }
                    selfCondition.signal();
                    if (!stop) {
                        prevCondition.await();
                    }

                } catch (InterruptedException e) {
                    e.printStackTrace();
                } finally {
                    lock.unlock();
                }
            }

            latch.countDown();
        }
    }
}
```

