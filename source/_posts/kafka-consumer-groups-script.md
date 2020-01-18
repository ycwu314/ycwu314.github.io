---
title: kafka-consumer-groups.sh 排查问题
date: 2020-01-18 15:39:15
tags: [kafka]
categories: [kafka]
keywords: [kafka consumer groups]
description: kafka-consumer-groups.sh 是个好用的工具。
---

# 背景

下游系统消费kafka消息数量和上游投递消息数量不一致。下游系统怀疑是kafka丢消息了（嗯，啥都不管，先让中间件背锅）。
<!-- more -->

# 排查问题

生产者到kafka，日志未见异常。
重点排查kafka到下游消费者这条链路。
消费者日志未见明显异常，接收到的消息都正常处理了。
于是让消费者改了一下，打印消息id和partition消息，看下哪些消息没有消费到。
结果发现有的partition一直消费不到。

怀疑是这些partition被分配到一些消费者去了。用`kafka-consumer-groups.sh`这个官方工具看下消费者的ip。（截图是后来补充的）
最后发现，有其他环境的起了相同的consumer group的消费者，因为是相同的cg，因此有的partition被意外的消费者消费了。。。
```
[root@bdgpu bin]# ./kafka-consumer-groups.sh  --bootstrap-server xxx.xxx.xxx.xxx:9092 --group yyy --describe
Note: This will only show information about consumers that use the Java consumer API (non-ZooKeeper-based consumers).


TOPIC              PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG      CONSUMER-ID                                       HOST             CLIENT-ID
req_zzzzzzz        1          2               2               0        consumer-5-cc48fa17-21e6-4c3b-9fb6-d209682ef849   /172.25.xxx.xxx     consumer-5
req_xxxxxxx        1          0               0               0        consumer-5-cc48fa17-21e6-4c3b-9fb6-d209682ef849   /172.25.xxx.xxx     consumer-5
req_test           1          3               3               0        consumer-5-cc48fa17-21e6-4c3b-9fb6-d209682ef849   /172.25.xxx.xxx     consumer-5
```
注意这里有一行提示：
>This will only show information about consumers that use the Java consumer API (non-ZooKeeper-based consumers)

老版本consumer的元数据信息是存储在zookeeper当中的，需要手动去zookeeper当中去修改偏移量。后来consumer的元数据信息存储在consumer-offsets。因此工具多了这行提示。
`kafka-consumer-groups.sh`另一个重要的用途是重置consumer offset，可以参见这个文章：[Kafka consumer group位移重设](https://www.cnblogs.com/huxi2b/p/7284767.html)

小结：
- 相同consumer group下的消费者被指派不同的partition来消费



