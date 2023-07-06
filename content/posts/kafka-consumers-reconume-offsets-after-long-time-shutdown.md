---
title: kafka消费者停机重启后重新消费offset的case
date: 2020-04-14 17:42:16
tags: [kafka]
categories: [kafka]
keywords: [kafka 消费者重复消费, offsets.retention.minutes]
description: offsets.retention.minutes 时间过短，可能导致消费者重复消费。
---


# 背景

线上一个项目使用了kafka。因为要做维护，**停机了一天多**，再次重启应用（kafka消费者），发现并没有从昨天提交的offset消费（对比应用日志文件），出现重复消费。
<!-- more -->
这个问题主要是同事排查，收获比较大，于是记录下来。

# 排查过程

显然是消费者commit offset没了。但是为什么没呢？另外，以前停机维护时间不超过一天，并没有发生这个问题。
kafka的consumer offset保存在`__consumer_offsets`这个topic（since kafka 0.9）。

这里有一篇重要的官方文章讲述相关offset retention问题：[Adjust default values of log.retention.hours and offsets.retention.minutes](https://issues.apache.org/jira/browse/KAFKA-3806)。

1. 为什么要设置`offsets.retention.minutes`?
kafka使用`__consumer_offsets`保存消费者offset。注意这是个topic，每次消费者commit offsets会写日志落盘。如果不清理日志，就会一直消耗磁盘直至撑爆。因此提供了选项来控制retention时间。
另外，如果一个消费者只出现一下，然后消失很长时间，也需要有机制清理掉日志。

2. 消费者不下线的话，就会一直保持最近提交的消费吗？
不会。如果消费者在线但是不消费消息、不提交offset，那么受`offsets.retention.minutes`影响，超过时间offset会被重置；与消费者是否在线无关。

3. `log.retention.hours`和`offsets.retention.minutes`的关系？
`log.retention.hours`日志消息保留时间。
`offsets.retention.minutes`是消费者offset保留时间。
如果`log.retention.hours` < `offsets.retention.minutes`，那么可能会出现消费者offset被清理、重复消费旧的日志。
因此，`offsets.retention.minutes` > `log.retention.hours`。

kafka 2.0以前，这两者的默认值是有问题的
```
default values of log.retention.hours (168 hours = 7 days) and offsets.retention.minutes (1440 minutes = 1 day) 
```

官网提到因为这2个默认组合的常见问题（对应开篇的问题）：
```
We have observed the following scenario and issue:

- Producing of data to a topic was disabled two days ago by producer update, topic wasn't deleted.
- Consumer consumed all data and properly committed offsets to Kafka.
- Consumer made no more offset commits for that topic because there was no more incoming data and there was nothing to confirm. (We have auto-commit disabled, I'm not sure how behaves enabled auto-commit.)
- After one day: Kafka cleared too old offsets according to offsets.retention.minutes.
- After two days: Long-term running consumer was restarted after update, it didn't find any committed offsets for that topic since they were deleted by offsets.retention.minutes so it started consuming from the beginning.
- The messages were still in Kafka due to larger log.retention.hours, about 5 days of messages were read again.
```

# 解决问题

确认现场没有配置`offsets.retention.minutes`，根据当前版本（0.9），默认值是1440分钟，即1天。
而停机维护时间恰好大于1天，导致消费者offset丢失。

修复：
- `server.properties`增加`offsets.retention.minutes`，配置为10天。
- 重启kafka server。

# 扩展话题

## `__consumer_offsets`

kafka 0.9之前，消费者offset是保存在zookeeper，但是zooKeeper并不适合大批量的频繁写入操作，会引发写入性能问题（因为zk的模型，写由一个master负责，并且同步到各个slave。offset提交性能受限于master的写入能力）。
因此0.9开始，默认把offset保存在kafka内部topic：`__consumer_offsets`。

## 频繁提交offsets可能引发的问题

消费者提交的offsets作为一条日志写入到`__consumer_offsets`。
系统默认每60s为consumer提交一次offset commit请求（由`auto.commit.interval.ms`, `auto.commit.enable`两个参数决定）。

如果每次消费一条消息就手动提交一次offsets，那么会产生大量的日志，迅速消耗磁盘空间。

解决：
- 使用异步提交，由offset manager管理
- 或者，同步提交，设置批量提交的最小处理消息数量
- 设置日志的清理策略
