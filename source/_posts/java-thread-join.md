---
title: Java Thread join 详解
date: 2019-08-24 21:24:36
tags: [java, 多线程, 高并发]
categories: [java]
keywords: [thread join, ensure_join]
description: Thread.join()挂起当前线程，直到目标线程结束，当前线程被唤醒。底层源码在线程exit的时候，通过ensure_join唤醒等待该线程的waiter。
---

# Thread join 例子

需求：一个线程去干点活，等工作结束后，通知主线程。
```java
public static void main(String[] args) {
    Thread t = new Thread(() -> {
        System.out.println("I am doing my job!");
        try {
            TimeUnit.SECONDS.sleep(6);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.out.println("job is done");
    });
    t.setName("my-job-thread");    
    t.start();
    System.out.println("all is done");
}
```
输出
```
all is done
I am doing my job!
job is done
```
显然，不符合要求。
<!-- more -->
其实只要增加一行代码即可：
```java
public static void main(String[] args) throws InterruptedException {
    Thread t = new Thread(() -> {
        System.out.println("I am doing my job!");
        try {
            TimeUnit.SECONDS.sleep(6);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.out.println("job is done");
    });
    t.setName("my-job-thread");
    t.start();
    // 划重点
    t.join();
    System.out.println("all is done");
}
```
输出
```
I am doing my job!
job is done
all is done
```

# Thread join 原理

加上join()方法后，main线程等待线程t结束后才继续执行。
如果jstack做thread dump：
{% asset_img v1_thread-join.png "java thread join" %}
main线程被挂起，等待唤醒。

Thread.join()的说明很简单明了：等待线程死亡。
```java
/**
* Waits for this thread to die.
*/
public final void join() throws InterruptedException {
    join(0);
}
```
再看看实际调用的join(long millis)：
```java
/**
* This implementation uses a loop of this.wait calls conditioned on this.isAlive. 
* As a thread terminates the this.notifyAll method is invoked. 
* It is recommended that applications not use wait, notify, or notifyAll on Thread instances.
*/
public final synchronized void join(long millis)
throws InterruptedException {
    long base = System.currentTimeMillis();
    long now = 0;
    if (millis < 0) {
        throw new IllegalArgumentException("timeout value is negative");
    }
    if (millis == 0) {
        while (isAlive()) {
            wait(0);
        }
    } else {
        while (isAlive()) {
            long delay = millis - now;
            if (delay <= 0) {
                break;
            }
            wait(delay);
            now = System.currentTimeMillis() - base;
        }
    }
}

/*
* Tests if this thread is alive. A thread is alive if it has been started and has not yet died.
*/
public final native boolean isAlive();
```

1. join(long millis)被synchronized修饰。实例方法级别的synchronized，表明要获取这个实例的监视器锁。因为里面的方法使用了wait()，因此要先获取监视器锁。
2. isAlive()返回线程是否死亡。
3. 只要线程还活着，就wait(0)一直等待。
4. 通常wait要通过notify来唤醒，但是t线程死亡后，自动唤醒了main线程，why？

ps. 关于synchronized、wait、notify，可以参见：
- {% post_link java-synchronized %}
- {% post_link java-wait-notify %}

明明是main线程调用t线程的join方法，好像要挂起的应该是t线程，但实际挂起的是main线程，有点反直觉？
其实不然。看看Object.wait()的javadoc
>Causes the current thread to wait until another thread invokes the notify() method or the notifyAll() method for this object. 

重点是**current thread**。  
sychronized只是为了获取监视器锁而已，挂起的是当前线程(上面例子，就是main线程)。

最大的疑问是，t线程死亡后，为什么能够唤醒main线程？Java代码明明没有使用notify啊。
java代码没有notify，那么可能就是底层jvm代码做了这个操作。
最终找到 [openjdk8 thread.cpp](http://hg.openjdk.java.net/jdk8/jdk8/hotspot/file/87ee5ee27509/src/share/vm/runtime/thread.cpp#l1729)：
```cpp
void JavaThread::exit(bool destroy_vm, ExitType exit_type) {
// more code

  // Notify waiters on thread object. This has to be done after exit() is called
  // on the thread (if the thread is the last thread in a daemon ThreadGroup the
  // group should have the destroyed bit set before waiters are notified).
  ensure_join(this);

// more code
}

static void ensure_join(JavaThread* thread) {
  // We do not need to grap the Threads_lock, since we are operating on ourself.
  Handle threadObj(thread, thread->threadObj());
  assert(threadObj.not_null(), "java thread object must exist");
  ObjectLocker lock(threadObj, thread);
  // Ignore pending exception (ThreadDeath), since we are exiting anyway
  thread->clear_pending_exception();
  // Thread is exiting. So set thread_status field in  java.lang.Thread class to TERMINATED.
  java_lang_Thread::set_thread_status(threadObj(), java_lang_Thread::TERMINATED);
  // Clear the native thread instance - this makes isAlive return false and allows the join()
  // to complete once we've done the notify_all below
  java_lang_Thread::set_thread(threadObj(), NULL);
  lock.notify_all(thread);
  // Ignore pending exception (ThreadDeath), since we are exiting anyway
  thread->clear_pending_exception();
}
```
线程exit的时候，会调用ensure_join()通知这个线程对象等待队列的waiter。ensure_join最终调用notify_all唤醒waiter。
因此，t线程结束，main线程被唤醒。

# Thread join 一个细节

join上的注释写明：
>It is recommended that applications not use wait, notify, or notifyAll on Thread instances.

因为使用了wait机制，因此当前线程最好使用wait，notfiy等方法。
Thread.join使用了while检查，避免虚假唤醒
```java
while (isAlive()) {
    wait(0);
}
```

# Thread join 小结

Thread.join()挂起当前线程。目标线程结束后再唤醒当前线程。
可以用于简单的线程等待。
最好使用FutureTask.get()之类的方法代替。