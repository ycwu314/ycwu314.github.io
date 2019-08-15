---
title: 聊聊sleep(0)和Thread.yield()
date: 2019-08-14 23:13:31
tags: [java, 多线程]
categories: [java]
keywords: [sleep 0 yeild, ConvertSleepToYield, ConvertYieldToSleep, convert yield sleep]
description: 
---

看到一个问题“sleep(0)的作用是什么”，发现底层牵涉还挺多内容。
以下基于openjdk8的源码，hg id 87ee5ee27509。

# java sleep和yield的源码

`Thread.sleep()`实现：[/src/share/vm/prims/jvm.cpp#l3038]( http://hg.openjdk.java.net/jdk8/jdk8/hotspot/file/87ee5ee27509/src/share/vm/prims/jvm.cpp#l3038)
```cpp
if (millis == 0) {
   // When ConvertSleepToYield is on, this matches the classic VM implementation of
   // JVM_Sleep. Critical for similar threading behaviour (Win32)
   // It appears that in certain GUI contexts, it may be beneficial to do a short sleep
   // for SOLARIS
   if (ConvertSleepToYield) {
     os::yield();
   } else {
     ThreadState old_state = thread->osthread()->get_state();
     thread->osthread()->set_state(SLEEPING);
     os::sleep(thread, MinSleepInterval, false);
     thread->osthread()->set_state(old_state);
   }
}
// more code
```

`Thread.yield()`实现：[/src/share/vm/prims/jvm.cpp#l3002](http://hg.openjdk.java.net/jdk8/jdk8/hotspot/file/87ee5ee27509/src/share/vm/prims/jvm.cpp#l3002)

```cpp
JVM_ENTRY(void, JVM_Yield(JNIEnv *env, jclass threadClass))
  JVMWrapper("JVM_Yield");
  if (os::dont_yield()) return;
#ifndef USDT2
  HS_DTRACE_PROBE0(hotspot, thread__yield);
#else /* USDT2 */
  HOTSPOT_THREAD_YIELD();
#endif /* USDT2 */
  // When ConvertYieldToSleep is off (default), this matches the classic VM use of yield.
  // Critical for similar threading behaviour
  if (ConvertYieldToSleep) {
    os::sleep(thread, MinSleepInterval, false);
  } else {
    os::yield();
  }
JVM_END
```

sleep(0)和yield的底层实现行为，由变量`ConvertSleepToYield`和`ConvertYieldToSleep`控制。并且使用平台相关的`os::yield()`或者`os::sleep()`。

<!-- more -->


# linxu平台

## os::sleep

`os::sleep`源码：[/src/os/linux/vm/os_linux.cpp#l3792](http://hg.openjdk.java.net/jdk8/jdk8/hotspot/file/87ee5ee27509/src/os/linux/vm/os_linux.cpp#l3792)
原码100来行，不贴了，简单说下：
- 先判断是否支持中断`interruptible`。
- 以可中断分支为例，退出条件是：被中断`os::is_interrupted(thread, true)`，或者时间到`millis <= 0`。否则通过`ParkEvent.park(millis)`阻塞等待millis之后返回，进入下一次循环。
```cpp
  ParkEvent * const slp = thread->_SleepEvent ;
// more code

      prevtime = newtime;

      {
        assert(thread->is_Java_thread(), "sanity check");
        JavaThread *jt = (JavaThread *) thread;
        ThreadBlockInVM tbivm(jt);
        OSThreadWaitState osts(jt->osthread(), false /* not Object.wait() */);

        jt->set_suspend_equivalent();
        // cleared by handle_special_suspend_equivalent_condition() or
        // java_suspend_self() via check_and_wait_while_suspended()

        slp->park(millis);

        // were we externally suspended while we were waiting?
        jt->check_and_wait_while_suspended();
      }
```
以后再对`ParkEvent`做介绍，此处不展开。

## os::yield

`os::yield`实现同样在os_linux.cpp
```cpp
int os::naked_sleep() {
  // %% make the sleep time an integer flag. for now use 1 millisec.
  return os::sleep(Thread::current(), 1, false);
}

void os::yield() {
  sched_yield();
}
```

找到[SCHED_YIELD](http://man7.org/linux/man-pages/man2/sched_yield.2.html)
>sched_yield() causes the calling thread to relinquish the CPU.  The thread is moved to the end of the queue for its static priority and a new thread gets to run.

## 小结

linux平台上：
- java sleep最终使用ParkEvent.park(mills)
- java yield使用sched_yield()

# windows平台

源码连接： [/src/os/windows/vm/os_windows.cpp](http://hg.openjdk.java.net/jdk8/jdk8/hotspot/file/87ee5ee27509/src/os/windows/vm/os_windows.cpp)
比较有意思的是Windows系统的yield和sleep的实现。

## sleep

见[Sleep function](https://docs.microsoft.com/zh-cn/windows/win32/api/synchapi/nf-synchapi-sleep)

>A value of zero causes the thread to relinquish the remainder of its time slice to any other thread that is ready to run. If there are no other threads ready to run, the function returns immediately, and the thread continues execution.Windows XP:  A value of zero causes the thread to relinquish the remainder of its time slice to any other thread of equal priority that is ready to run. If there are no other threads of equal priority ready to run, the function returns immediately, and the thread continues execution. This behavior changed starting with Windows Server 2003.

sleep(0)会使该thread放弃拥有的剩余时间片。

## yield

.net 4.0版本以后增加了[Thread.Yield Method](https://docs.microsoft.com/en-us/dotnet/api/system.threading.thread.yield?redirectedfrom=MSDN&view=netframework-4.8#System_Threading_Thread_Yield)

>If this method succeeds, the rest of the thread's current time slice is yielded. The operating system schedules the calling thread for another time slice, according to its priority and the status of other threads that are available to run.
>
>Yielding is limited to the processor that is executing the calling thread. The operating system will not switch execution to another processor, even if that processor is idle or is running a thread of lower priority. If there are no other threads that are ready to execute on the current processor, the operating system does not yield execution, and this method returns false.
>
>This method is equivalent to using platform invoke to call the native Win32 SwitchToThread function. You should call the Yield method instead of using platform invoke, because platform invoke bypasses any custom threading behavior the host has requested.

注意yield的时间片只能被同一个处理的线程使用。

## 小结

Windows平台：
- sleep(0)和yield()都会尝试释放当前线程剩余的时间片，并且通知调度器让合适的线程使用该时间片。
- yield限制是当前处理器的其他线程才能使用剩余的时间片，sleep没有这个限制。

# 总结

- sleep(0)和yield的实现，受具体的jvm版本和os影响。
- yield通常会使用`os::yield()`实现，通知scheduler让其他线程使用时间片。
- sleep(0)则不一定会触发yield的语义。要释放时间片，通常用yield就好了。

# 参考

- [Java线程源码解析之yield和sleep](https://www.jianshu.com/p/0964124ae822)
- [Thread.Sleep(0) vs Sleep(1) vs Yeild](https://www.cnblogs.com/stg609/p/3857242.html)



