---
title: 反应式编程系列2： Flux和Mono
date: 2020-11-27 15:04:16
tags: [reactive, 反应式编程]
categories: [反应式编程]
keywords:
description: Flux和Mono简介。
---

在反应式编程中，最核心的组件是发布者Publisher和订阅者Subscriber。
今天介绍的是Publisher中的Flux和Mono。
{% asset_img pub-sub.png %}
<!-- more -->

# Flux和Mono简介

`Publisher<T>`是一个可以提供0-N个序列元素的提供者，并根据其订阅者`Subscriber<? super T>`的需求推送元素。

发布者发布元素信号（onNext）、完成信号（onComplete）、错误信号（onError）。
订阅者接受这3种信号，并进行消费。
其中完成信号、错误信号都会终止流。
{% asset_img reactive-stream-flow.png %}


在reactor里，Flux和Mono都是publisher。
{% asset_img flux-mono-hierarchy.png %}

Flux 是一个发出(emit) 0-N 个元素组成的异步序列的Publisher，可以被onComplete信号或者onError信号所终止。
Mono 是一个发出(emit)0-1个元素的Publisher，可以被onComplete信号或者onError信号所终止。

# 流的基本用法

使用webflux作为演示环境。
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
    <version>2.4.0</version>
</dependency>
```

首先要创建数据流。
```java
// 接受 0..N 个输入
Flux.just(1, 2, 3).subscribe(System.out::println);

// 范围，start、count
Flux.range(1, 5).subscribe(System.out::println);

// 从数组创建
Flux.fromArray(new String[]{"a", "b", "c"}).subscribe(System.out::println);

// 从stream创建
Flux.fromStream(Arrays.asList(1, 2, 3).stream()).subscribe(System.out::println);

// 从集合创建
Flux.fromIterable(Arrays.asList(1, 2, 3)).subscribe(System.out::println);

// 空元素
Flux.empty().doOnComplete(() -> System.out.println("complete on empty")).subscribe();
Flux.just();
```

可以从一个流创建另一个流：
```java
Flux a = Flux.just(1, 2, 3);
Flux b = Flux.from(a);
a.subscribe(i -> System.out.println("a: " + i));
b.subscribe(i -> System.out.println("b: " + i));
```

甚至可以从CompletableFuture创建(仅限于Mono)：
```java
CompletableFuture<Integer> f = new CompletableFuture<>();
Mono.fromFuture(f).subscribe(System.out::println);
f.complete(999);
```

发布者也支持创建错误流：
```java
// 错误流
Flux.error(new RuntimeException("err happened")).subscribe();
```

上面提到发布者提供了信号支持，对应`doOnXXX`方法。
```java
// 完成信号
Flux.empty().doOnComplete(() -> System.out.println("complete on empty")).subscribe();
```

流可以合并：
```java
Flux.just(1, 2, 3)
        .concatWith(Mono.error(new RuntimeException()))
        .onErrorReturn(999)
        .concatWith(Flux.just(4))
        .subscribe(
                System.out::println,
                System.err::println,
                () -> System.out.println("Completed!"));
```

创建流之后，可以使用中间转换函数，例如filter、map、flatMap、then、zip、reduce 等（和java 8 stream相似）。

最后使用subscribe方法触发订阅。

# 流的高级操作

## create

create可以自定义创建元素的方式。
```java
// 输出20以内的奇数
Flux.create(emitter -> {
    for (int i = 1; i < 20; i += 2) {
        emitter.next(i);
    }
    emitter.complete();
}).subscribe(System.out::println);
```


## defer函数

`defer`是懒初始化，**每次**subscribe的时候都会调用supplier获取publisher实例。
如果Supplier每次返回的实例不同，则可以构造出和subscribe次数相关的Flux源数据流。
如果每次都返回相同的实例，则和from(Publisher<? extends T> source)效果一样。

```java
@Test
public void testDefer() {
    Flux a = Flux.just(new Date());
    Flux b = Flux.defer(() -> Flux.just(new Date()));

    a.subscribe(i -> System.out.println("a\t" + i));
    b.subscribe(i -> System.out.println("b\t" + i));

    try {
        Thread.sleep(3000L);
    } catch (InterruptedException e) {
        e.printStackTrace();
    }

    a.subscribe(i -> System.out.println("a\t" + i));
    b.subscribe(i -> System.out.println("b\t" + i));
}
```

```
a	Wed Dec 23 17:09:32 CST 2020
b	Wed Dec 23 17:09:32 CST 2020
a	Wed Dec 23 17:09:32 CST 2020
b	Wed Dec 23 17:09:35 CST 2020
```
两次订阅a流，数据一致。
第二次订阅b流，又执行`new Date()`得到元素，因此两次订阅数值不一样。

## buffer

缓冲value，打包到一个List，再发射。
```java
Flux.range(1, 17).buffer(5).subscribe(System.out::println);

// 输出
[1, 2, 3, 4, 5]
[6, 7, 8, 9, 10]
[11, 12, 13, 14, 15]
[16, 17]
```

## interval

以一定时间间隔发射元素。
```java
// 从 0 开始递增的 Long 对象的序列
Flux.interval(Duration.ofMillis(100L)).subscribe(System.out::println);
try {
    Thread.sleep(1000);
} catch (InterruptedException e) {
    e.printStackTrace();
}
```


## share

共享流，实现多播
```java
// share： 
// Returns: a Flux that upon first subscribe causes the source Flux to subscribe once, late subscribers might therefore miss items.

Flux a = Flux.interval(Duration.ofMillis(200)).share();
Flux b = Flux.from(a);
b.subscribe(i -> System.out.println("b: " + i));
try {
    Thread.sleep(1000L);
} catch (InterruptedException e) {
    e.printStackTrace();
}

// 注意：在开始新的共享流之前的信号都丢失了
// 这里c的输出丢失了0 ~ 4
Flux c = Flux.from(a);
c.subscribe(i -> System.out.println("c: " + i));
try {
    Thread.sleep(1000L);
} catch (InterruptedException e) {
    e.printStackTrace();
}
```

输出
```
b: 0
b: 1
b: 2
b: 3
b: 4
b: 5
c: 5
b: 6
c: 6
b: 7
c: 7
b: 8
c: 8
b: 9
c: 9
```


## cache

将此Flux转换为热源，并为进一步的用户缓存最后发射的信号。将保留一个无限量的OnNeXT信号。完成和错误也将被重放。

改造上面share的例子
```java
// 增加调用cache()
Flux a = Flux.interval(Duration.ofMillis(200)).share().cache();
Flux b = Flux.from(a);
b.subscribe(i -> System.out.println("b: " + i));
try {
    Thread.sleep(1000L);
} catch (InterruptedException e) {
    e.printStackTrace();
}

// 注意：在开始新的共享流之前的信号都丢失了
// 这里c的输出丢失了0 ~ 4
Flux c = Flux.from(a);
c.subscribe(i -> System.out.println("c: " + i));
try {
    Thread.sleep(1000L);
} catch (InterruptedException e) {
    e.printStackTrace();
}
```

输出
```
b: 0
b: 1
b: 2
b: 3
b: 4
c: 0
c: 1
c: 2
c: 3
c: 4
b: 5
c: 5
b: 6
c: 6
b: 7
c: 7
b: 8
c: 8
b: 9
c: 9
```

参考资料：[FLUX CACHING IN PROJECT REACTOR: REPLAYING PAST DATA](https://www.reactiveprogramming.be/project-reactor-flux-caching/)

使用cache可以支持高并发场景。

## collect

把Flux流转为Mono。
```java
Mono<List<Integer>> a = Flux.just(1, 2, 3).collectList();
a.subscribe(System.out::println);
```

## distinct

对于每一个Subscriber，跟踪已经从这个Flux 跟踪元素和过滤出重复。
值本身被记录到一个用于检测的哈希集中。如果希望使用distinct(Object::hashcode)更轻量级的方法，该方法不保留所有对象，但是更容易由于hashcode冲突而错误地认为两个元素是不同的。

```java
Flux.just(1, 1, 2, 3, 4, 5, 2).distinct().subscribe(System.out::println);
```

## doOnNext

在发射元素之前执行动作
```
Flux.just(1, 2, 3).doOnNext(i -> System.out.println("***")).subscribe(System.out::println);
```

输出
```
***
1
***
2
***
3
```

# 流的高级操作2

## map, flatMap, then

map和flatMap是常见的中间转换函数。
```java
Flux.just(1, 2, 3).map(i -> i * i).subscribe(System.out::println);
System.out.println("*****");
Flux.just(1, 2, 3).flatMap(i -> Flux.just(i * i).delayElements(Duration.ofSeconds(1)))
        .subscribe(System.out::println);

try {
    Thread.sleep(5000);
} catch (InterruptedException e) {
    e.printStackTrace();
}
```

map函数是同步转换元素
```java
map(Function<? super T, ? extends V> mapper) 
```

flatMap函数是异步转换元素，因此Function必须是Publisher类型
```java
flatMap(Function<? super T, ? extends Publisher<? extends R>> mapper)
```

另一个常见的操作是then
```java
Flux.just(1, 2, 3).then(Mono.just(999)).subscribe(System.out::println);
```

输出
```
999
```

then并不是等待上一个流的操作，而是直接丢弃，这和一般语义上的then操作不一样。


## zipWith

{% asset_img zipWith.png %}

zip原意是“拉链”。
zipWith操作可以合并两个流，结果为Tuple2。因为合并，只对位置相同的元素操作，多余元素被丢掉。

```java
Flux a = Flux.just(1, 2, 3, 4, 5, 6, 7);
Flux b = Flux.just("a", "b", "c");
a.zipWith(b).subscribe(System.out::println);
```

输出
```
[1,a]
[2,b]
[3,c]
```

## expand, expandDeep

基于一个递归的生成序列的规则扩展每一个元素，然后合并为一个序列发出：
- 广度优先：expand(Function)
- 深度优先：expandDeep(Function)

用于遍历树形结构是很方便的。

假设树的结构如下
```
A
 - AA
   - aa1
B
 - BB
   - bb1
```

先定义节点
```java
@Data
@AllArgsConstructor
static class Node {
    private String id;
    private Node next;
}
```
然后初始化这棵树
```java
Node aa1 = new Node("aa1", null);
Node aa = new Node("AA", aa1);
Node a = new Node("A", aa);
Node bb1 = new Node("bb1", null);
Node bb = new Node("BB", bb1);
Node b = new Node("B", bb);
```

广度优先
```java
Flux.just(a, b).expand(i -> {
    if (i.next != null) {
        return Mono.just(i.next);
    } else {
        return Mono.empty();
    }
}).subscribe(i -> System.out.println(i.getId()));
```
输出
```
A
B
AA
BB
aa1
bb1
```

深度优先
```java
Flux.just(a, b).expandDeep(i -> {
    if (i.next != null) {
        return Mono.just(i.next);
    } else {
        return Mono.empty();
    }
}).subscribe(i -> System.out.println(i.getId()));
```
输出
```
A
AA
aa1
B
BB
bb1
```

# 辅助功能

观察所有stream的信号，并且输出到日志
```java
Flux.just(1,2,3).log().subscribe(System.out::println);
```

输出
```
16:52:29.605 [main] INFO reactor.Flux.Array.1 - | onSubscribe([Synchronous Fuseable] FluxArray.ArraySubscription)
16:52:29.613 [main] INFO reactor.Flux.Array.1 - | request(unbounded)
16:52:29.613 [main] INFO reactor.Flux.Array.1 - | onNext(1)
1
16:52:29.613 [main] INFO reactor.Flux.Array.1 - | onNext(2)
2
16:52:29.613 [main] INFO reactor.Flux.Array.1 - | onNext(3)
3
16:52:29.614 [main] INFO reactor.Flux.Array.1 - | onComplete()
```


# 参考

- [Spring Reactor 入门与实践](https://www.jianshu.com/p/7ee89f70dfe5)


