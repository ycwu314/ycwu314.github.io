---
title: wait、notify和生产者消费者模式
date: 2019-08-18 21:01:38
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [虚假唤醒, java wait notify, wait notify 生产者 消费者, notfiy vs notifyAll, IllegalMonitorStateException, 线程间通信]
description: wait、notify、notifyAll在使用之前都要先进入synchronized，否则抛出IllegalMonitorStateException。notify随机唤醒一个线程，notifyAll唤醒全部线程。虚假唤醒问题，要循环检测判断条件，不能直接if判断。
---

wait、notify、notifyAll定义在Object类，是java提供的线程间通信机制。
wait、notify、notifyAll使用了监视器锁实现同步，因此使用之前要先获取监视器锁（即synchronized），否则抛出IllegalMonitorStateException异常。
<!-- more -->
# 生产者消费者模式

线程间通信典型的例子是生产者消费者模式。

```java
public class WaitAndNotify {

    private static int MAX_SIZE = 8;

    public static void main(String[] args) {
        LinkedList<Integer> holders = new LinkedList();
        new Thread(new Producer(holders)).start();
        new Thread(new Consumer(holders)).start();
    }

    static class Consumer implements Runnable {
        
        private LinkedList<Integer> holders;

        public Consumer(LinkedList<Integer> holders) {
            this.holders = holders;
        }

        @Override
        public void run() {
            while (true) {
                synchronized (holders) {
                    if (holders.size() == 0) {
                        holders.notify();
                    } else {
                        System.out.println("consumes: " + holders.removeFirst());
                        try {
                            Thread.sleep(500);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                }
            }
        }
    }

    static class Producer implements Runnable {


        private LinkedList<Integer> holders;

        public Producer(LinkedList<Integer> holders) {
            this.holders = holders;
        }

        @Override
        public void run() {
            Random random = new Random();

            while (true) {
                synchronized (holders) {
                    if (holders.size() < MAX_SIZE) {
                        int x = random.nextInt(100);
                        System.out.println("produce: " + x);
                        holders.add(x);
                        try {
                            Thread.sleep(500);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    } else {
                        try {
                            holders.wait();
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                }
            }
        }
    }
}
```

# notify vs notifyAll

notify随机唤醒一个等待的线程。
notifyAll唤醒全部等待的线程。

# 虚假唤醒 spurious wakeup

来自 https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html#wait%28%29 ：

>A thread can also wake up without being notified, interrupted, or timing out, a so-called spurious wakeup. While this will rarely occur in practice, applications must guard against it by testing for the condition that should have caused the thread to be awakened, and continuing to wait if the condition is not satisfied. In other words, waits should always occur in loops, like this one:

这里有篇扩展的资料，讲述linux上PTHREAD_COND_TIMEDWAIT和虚假唤醒的问题，[PTHREAD_COND_TIMEDWAIT](http://man7.org/linux/man-pages/man3/pthread_cond_timedwait.3p.html)：

>Some implementations, particularly on a multi-processor, may
>sometimes cause multiple threads to wake up when the condition
>variable is signaled simultaneously on different processors.
>
>In general, whenever a condition wait returns, the thread has to re-
>evaluate the predicate associated with the condition wait to
>determine whether it can safely proceed, should wait again, or should
>declare a timeout. A return from the wait does not imply that the
>associated predicate is either true or false.

一些obj.wait()会在除了obj.notify()和obj.notifyAll()的其他情况被唤醒，而此时是不应该唤醒的。
为了处理虚假唤醒的case，要在while中循环判断条件是否成立，不能直接if判断就了事。

```java
synchronized (obj) {
    while (<condition does not hold>)
        obj.wait(timeout);
    ... // Perform action appropriate to condition
}
```