---
title: 反应式编程系列4：backpressure
date: 2020-12-17 17:49:56
tags: [reactive, 反应式编程]
categories: [反应式编程]
keywords:
description: backpressure是应对生产者消费者速率不一致的一种方式。
---

backpressure是一种现象：生产速率高于消费速率，消费者通知生产者降低产生信号速率。
backpressure这种协调机制对于维持系统稳定具有重要作用。
<!-- more -->

生产速率和消费速率不匹配是一个普遍存在的现象。严重者会产生大量信号积压、请求SLA得不到满足、甚至压垮消费者。
通常有几种策略处理：
- 缓冲。消费者缓冲多余请求。然而缓冲队列会消耗资源，因此不应该是无界的。另外，在缓冲队列中的信号，得不到及时处理，SLA得不到保障。
- 流控。消费者通知生产者，降低生产速率。
- 丢弃。

缓冲队列大小是有限的，一旦填满，就面临流控或者丢弃。
backpressure是对应流控的一个方式。
在了解backpressure之前，先要了解“冷信号与热信号”。

# 冷信号与热信号

.NET框架Reactive Extensions(RX) 提出了Hot Observable和Cold Observable的概念：
>Hot Observable是主动的，尽管你并没有订阅事件，但是它会时刻推送，就像鼠标移动；而Cold Observable是被动的，只有当你订阅的时候，它才会发布消息。
>Hot Observable可以有多个订阅者，是一对多，集合可以与订阅者共享信息；而Cold Observable只能一对一，当有不同的订阅者，消息是重新完整发送。

任何的信号转换即是对原有的信号进行订阅从而产生新的信号。

>冷信号类似于拉取模型，通常都是接收到请求后才生成信号，所以一般不存在背压的问题（如网络请求等）。
>而热信号则是会主动产生数据（推送模型，不管消费者是否请求，如鼠标移动事件等），当热信号产生的速度远大于订阅者消费的速度，就会产生不平衡，过多的热信号会挤压，这时就需要一种背压策略来解决这个问题。

# 流控方式

常见的流控方式：
- Callstack blocking 调用链阻塞
- backpressure 背压/反压

调用链阻塞的一个例子是，java线程池的拒绝策略。当缓冲队列满了、切拒绝策略为caller_run，那么生产者将不能向线程池提交任务。
另一种流控方法是backpressure。消费者主动通知生产者减少发送数据。例如tcp协议的接收窗口。


# backpressure

backpressure，也称为Reactive Pull，下游根据自己接收窗口的情况来控制接收速率，并通过反向的request请求控制上游的发送速率。

拉模式实现的反压比较简单。
生产者和消费者通过Subscription(订阅)关联。
消费者通过`Subscription#request(n)`向生产者请求n个消息。
生产者通过`onNext()`向消费者发送消息。

```java
        Flux.range(1, 21).log().subscribe(new Subscriber<Integer>() {

            private int threshold = 5;
            private int fetchSize = 3;
            private Subscription subscription;
            private int processedCount = 0;

            @Override
            public void onSubscribe(Subscription subscription) {
                this.subscription = subscription;
                this.subscription.request(fetchSize);
            }

            @Override
            public void onNext(Integer obj) {
                processedCount++;

                if (processedCount > threshold) {
                    System.out.println("*** slow down for a while...");
                    try {
                        Thread.sleep(3000);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                    processedCount = 0;
                    subscription.request(1);
                } else {
                    subscription.request(fetchSize);
                }
            }

            @Override
            public void onError(Throwable throwable) {

            }

            @Override
            public void onComplete() {

            }
        });
```
输出
```
17:16:54.954 [main] INFO reactor.Flux.Range.1 - | onSubscribe([Synchronous Fuseable] FluxRange.RangeSubscription)
17:16:54.959 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:54.959 [main] INFO reactor.Flux.Range.1 - | onNext(1)
17:16:54.959 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:54.959 [main] INFO reactor.Flux.Range.1 - | onNext(2)
17:16:54.959 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:54.959 [main] INFO reactor.Flux.Range.1 - | onNext(3)
17:16:54.959 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:54.959 [main] INFO reactor.Flux.Range.1 - | onNext(4)
17:16:54.960 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:54.960 [main] INFO reactor.Flux.Range.1 - | onNext(5)
17:16:54.960 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:54.960 [main] INFO reactor.Flux.Range.1 - | onNext(6)
*** slow down for a while...
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | request(1)
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | onNext(7)
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | onNext(8)
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | onNext(9)
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | onNext(10)
17:16:57.960 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:57.961 [main] INFO reactor.Flux.Range.1 - | onNext(11)
17:16:57.961 [main] INFO reactor.Flux.Range.1 - | request(3)
17:16:57.961 [main] INFO reactor.Flux.Range.1 - | onNext(12)
*** slow down for a while...
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | request(1)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | onNext(13)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | request(3)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | onNext(14)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | request(3)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | onNext(15)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | request(3)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | onNext(16)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | request(3)
17:17:00.961 [main] INFO reactor.Flux.Range.1 - | onNext(17)
17:17:00.962 [main] INFO reactor.Flux.Range.1 - | request(3)
17:17:00.962 [main] INFO reactor.Flux.Range.1 - | onNext(18)
*** slow down for a while...
17:17:03.963 [main] INFO reactor.Flux.Range.1 - | request(1)
17:17:03.963 [main] INFO reactor.Flux.Range.1 - | onNext(19)
17:17:03.963 [main] INFO reactor.Flux.Range.1 - | request(3)
17:17:03.963 [main] INFO reactor.Flux.Range.1 - | onNext(20)
17:17:03.963 [main] INFO reactor.Flux.Range.1 - | request(3)
17:17:03.963 [main] INFO reactor.Flux.Range.1 - | onNext(21)
17:17:03.963 [main] INFO reactor.Flux.Range.1 - | request(3)
17:17:03.964 [main] INFO reactor.Flux.Range.1 - | onComplete()
```

生产者端支持的背压策略：
- onBackpressureBuffer
- onBackpressureDrop
- onBackpressureError
- onBackpressureLatest

# 小结

因为现实场景是不可预估的，生产速度总是有一定的可能会大于下游消费的速度，所以 Buffer 是永远需要的。
Buffer要使用有界队列。无界buffer会消耗大量内存，导致生产者不稳定。


# 参考

- [如何形象的描述反应式编程中的背压(Backpressure)机制？](https://www.zhihu.com/question/49618581)
- [背压(Back Pressure)与流量控制](https://lotabout.me/2020/Back-Pressure/)
- [细说ReactiveCocoa的冷信号与热信号（二）：为什么要区分冷热信号](https://tech.meituan.com/2015/09/28/talk-about-reactivecocoas-cold-signal-and-hot-signal-part-2.html)
