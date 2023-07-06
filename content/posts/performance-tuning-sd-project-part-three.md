---
title: SD项目：高并发的性能优化，part 3
date: 2019-06-13 11:05:21
tags: [java, 性能调优, SD项目, 高并发]
categories:  SD项目
keywords: [性能调优, 高并发, TieredCompilation]
---
总结SD项目的性能优化过程和思考，part 3。

往期文章
- [performance-tuning-sd-project-part-one](/posts/performance-tuning-sd-project-part-one)
- [performance-tuning-sd-project-part-two](/posts/performance-tuning-sd-project-part-two)

# 启动负载优化

每次更新重启应用后压测，cpu load较高，RT较大，随后下降并稳定下来。
<!-- more -->
## 分析&解决

这是一个典型的问题，java应用重启后一段时间，如果请求tps很高，那么load会很高。
一般的JVM实现，会采用解释器+编译器编译方式来提高性能。解释器负责翻译java字节码，运行性能一般。编译器则会把**热点**代码翻译成native code，运行性能高，但是会产生编译时间开销。JVM根据应用runtime的采样统计，识别热点代码，并且进行编译优化。

热点代码发现后，由编译器线程负责编译，和应用线程竞争使用cpu资源。编译器线程数由`-XX:CICompilerCount`。查看jvm启动参数，发现被写死了`-XX:CICompilerCount=2`，和容器cpu配置相比，明显少了。

<!-- more -->

## 数据对比

更新`CICompilerCount`，重启后压测。短时间cpu load更高，但是比之前更快的下降。

## 扩展

jvm编译器分为C1和C2。C1的编译速度快，C2的编译速度慢，但是机器码性能比C1好。
java还有分层编译技术`TieredCompilation`，在编译速度和机器码性能之间权衡：
- Level 0 – interpreted code
- Level 1 – simple C1 compiled code (with no profiling)
- Level 2 – limited C1 compiled code (with light profiling)
- Level 3 – full C1 compiled code (with full profiling)
- Level 4 – C2 compiled code (uses profile data from the previous steps)

java8以后默认开启`-XX:+TieredCompilation`。


# 房间服务拆分

大小房间共用mq topic、数据库、缓存等资源。测试典型场景下大房间被小房间影响的程度。

## 优化前

1个大房间 + 2000个小房间同时运行，观察大房间轮转时间，偶尔有1s到2s的卡顿。

## 分析&解决

正常场景，高峰期是一个大房间，加上很多个小房间同时运行。大房间人数多，发生卡顿延迟会影响大量用户的体验，后果比小房间严重多。
一个房间只要在轮转，那么就会产生1条延迟mq消息，延迟队列本身会有轻微堆积。另外还要考虑每条消息的消费耗时，大概在10-100ms。
增加消费者实例、消费者线程是提高消费速度的一个方式。但是更直接的方式是拆分topic，避免堆积。
至于数据库、缓存资源，目前tps足够，暂时不考虑拆分。

## 数据对比

拆分topic后，1个大房间 + 2000个小房间同时运行，大房间没有卡顿。


## 思考

关键业务单独拆分资源，保证可用性。后续对房间服务进行重构，拆分成大房间、小房间服务，单独演化。

