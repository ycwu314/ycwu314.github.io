---
title: 延迟消息策略
date: 2019-07-08 09:36:01
tags: [RocketMQ, SD项目]
categories: SD项目
keywords: [延迟消息, RocketMQ]
description: 
---

上次分析了RocketMQ的延迟消息机制。要注意的是，RocketMQ的是延迟消息，并非任意精度的定时消息。如果业务上需要任秒级别意精度的定时消息，就要做workaround的办法了。

往期文章：
- {% post_link rocketmq-delay-message %}

我的设计思路是：
1. 延迟消息body增加`expectExecuteAt`字段，表明期望的执行时间
2. 计算最近的、未开始的delayTimeLevel。例如，期望延迟6s，最近的延迟时间是5s
3. 在消费者端，增加延迟消息处理策略，根据当前时间和消息的`expectExecuteAt`字段进行处理。

延迟消息处理策略：
- 立即执行。消息已经到达执行时间，或者接近处理时间（比如小于1000s）、可以提前执行。
- 再投递。还没到达执行时间，重新计算delayTimeLevel，再次发送延迟消息。
- 本地队列。还没到达执行时间，缓冲到本地Scheduled队列。如果此时jvm重启，会有丢失消息处理的风险，但性能要比再投递好。
- 丢弃。异常情况下，消息已经过时很久，处理消息已经不产生业务意义。

不过实际业务中，并没有采用延迟消息处理策略，而是在业务层上做折中设计。