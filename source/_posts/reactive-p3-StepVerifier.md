---
title: 反应式编程系列3：使用StepVerifier进行单元测试
date: 2020-12-17 11:27:44
tags: [reactive, 反应式编程]
categories: [反应式编程]
keywords:
description: 使用StepVerifier进行单元测试
---

流是动态数据，如何做单元测试？
StepVerifier通过订阅流，然后消费其产生的信号，逐个比较元素、错误信号、完成信号等，从而解决单元测试问题。
<!-- more -->

# 基本用法

先发射1，然后发射2，最后产生error。
```java
@Test
public void testStepVerifier() {
    Flux a = Flux.just(1, 2, 3, 4).concatWith(Mono.error(new RuntimeException("err")));
    StepVerifier.create(a)
            .expectNext(1)
            .expectNext(2)
            .expectNext(3, 4)
            .expectError(RuntimeException.class)
            .verify();
}
```

期望流正常结束
```java
Flux a = Flux.just(1, 2, 3, 4);
StepVerifier.create(a)
        .expectNext(1, 2, 3, 4)
        .expectComplete()
        .verify();
```

判断元素是否符合一些特性
```java
Flux a = Flux.just("a", "aa", "a2323");
StepVerifier.create(a)
        .expectNextMatches(i -> ((String) i).startsWith("a"))
        .expectNextMatches(i -> ((String) i).startsWith("a"))
        .expectNextMatches(i -> ((String) i).startsWith("a"))
        .expectComplete()
        .verify();
```

如果流的元素很多，逐个`expectNext()`显然不合适；使用`thenConsumeWhile()`替代：
```java
int max = 1000;
Flux a = Flux.range(1, max);
StepVerifier.create(a)
        .thenConsumeWhile(o -> ((Integer) o) <= max)
        .expectComplete()
        .verify();
```

# 处理时间问题

流的数据是动态的，可能间隔一段时间才到来，怎么加快单元测试的执行速度？

StepVerifier使用VirtualTimeScheduler来解决上面问题：
>Prepare a new StepVerifier in a controlled environment using `VirtualTimeScheduler` to manipulate a virtual clock via `StepVerifier.Step.thenAwait`. 
>The scheduler is injected into all `Schedulers` factories, 
>which means that any operator created within the lambda without a specific scheduler will use virtual time. 


```java
StepVerifier.withVirtualTime(() -> Flux.range(1, 10).delayElements(Duration.ofMinutes(1)))
        // 触发订阅
        .expectSubscription()
        // 触发时间飞逝
        .thenAwait(Duration.ofSeconds(30))
        .expectNextCount(0)
        .thenAwait(Duration.ofSeconds(10))
        // 期望一段时间内没有事件
        .expectNoEvent(Duration.ofSeconds(10))
        .thenAwait(Duration.ofMinutes(100))
        .expectNextCount(10)
        .expectComplete()
        .verify();
```


# 参考

- [Reactor的测试——响应式Spring的道法术器](https://blog.csdn.net/get_set/article/details/79611380)