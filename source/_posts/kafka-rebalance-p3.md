---
title: kafka rebalance系列：static membership优化
date: 2020-04-21 14:55:32
tags: [kafka]
categories: [kafka]
keywords: [kafka static membership, kafka group.instance.id]
description: kafka 2.3增加group.instance.id配置，支持对client静态化配置id，减少client重启后加入group导致rebalance。
---

# rebalance 流程

在了解static membership优化之前，先简单学习rebalance流程（kafka 2.3以前）。
这篇文章对理解rebalance流程很有帮助，推荐阅读：[Apache Kafka Rebalance Protocol, or the magic behind your streams applications](https://medium.com/streamthoughts/apache-kafka-rebalance-protocol-or-the-magic-behind-your-streams-applications-e94baf68e4f2)。

<!-- more -->
下面图片都是来自这篇文章。

## JoinGroup

当一个consumer启动，通过向kafka broker coordinator发送`FindCoordinator`请求找到group  coordinator，然后发送`JoinGroup`。
{% asset_img join-group.png join-group %}
注意请求带上了`session.timeout.ms`和`max.poll.interval.ms`，协助coordinator踢出超时的client。

`JoinGroup`请求，使得coordinator进入屏障，在`min(rebalance timeout, group.initial.rebalance.delay.ms)`时间内，等待收集其他consumer发送的`JoinGroup`请求。

group内第一个consumer被选作group leader。coordinator向leader发送`JoinGroup`响应，包含当前活跃成员列表。其他成员收到空响应。
group leader负责partition分配。
{% asset_img join-group-2.png join-group-2 %}

## SyncGroup

所有成员向coordinator发送`SyncGroup`请求。
其中，group leader的`SyncGroup`请求包含了partition分配结果。
其他成员的`SyncGroup`请求是空请求。
{% asset_img sync-group.png sync-group %}

coordinator响应所有的`SyncGroup`请求。每个consumer收到响应后，知道自己分配到的partition，监听分区并且拉取消息。
{% asset_img sync-group-2.png sync-group-2 %}

## Heartbeat

consumer后台线程发送心跳：`heartbeat.interval.ms`。

在rebalance阶段，coordinator收到心跳信息，则认为这个consumer需要rejoin。

{% asset_img heartbeat.png heartbeat %}

coordinator通知其他consumer，在下一个heartbeat周期，进行JoinGroup、SyncGroup操作。
{% asset_img rejoin.png rejoin %}

在整个rebalance阶段，在重新分区之前，consumer都不会再处理任何消息。
默认的rebalance timeout (`max.poll.interval.ms`)为5min，是非常长的，会导致产生很大的consumer-lag。

# consumer滚动更新的问题

>Transient failures are those that occur temporarily and for a short period of time.

并非所有的consumer异常都需要触发rebalance。它们可能稍后就会重新加入group，比如滚动升级。

而当一个新的成员加入group，请求里面不包含任何membership信息。Coordinator分配一个UUID作为此成员id，并且缓存起来。这个consumer后续的生命周期内，都会使用这个member id。那么这个consumer rejoin的时候不会触发rebalance。

但是，一个刚刚重启的consumer，本地内存里面没有member id或者generation id。因此它重新加入group，会触发rebalance。GroupCoordinator也不保证原来这个member处理的分区会被重新分配回去。

于是问题变为：如何在重启之后，还能正常识别consumer。

{% asset_img restart.png restart %}

# KIP-345 static membership

为了解决这个问题，KIP-345增加static membership特性：增加`group.instance.id`选项（client端）。Group instance id是用户指定的、区分不同client的标识。
现在GroupCoordinator识别一个consumer，可以通过
- coordinator-assigned member ID （client重启后丢失）
- `group.instance.id` （client重启后不丢失）

有了static membership之后，触发consumer group rebalace的条件:
- A new member joins
- A leader rejoins (possibly due to topic assignment change)
- An existing member offline time is over session timeout
- Broker receives a leave group request containing a list of `group.instance.id`s 

为了使用static membership配置，需要server和client都升级到kafka 2.3版本。

开启static membership之后，还要考虑`session.timeout.ms`是否足够大。
>When using static membership, it’s recommended to increase the consumer property `session.timeout.ms` large enough so that the broker coordinator will not trigger rebalance too frequently.

# 参考

- [KIP-345: Introduce static membership protocol to reduce consumer rebalances](https://cwiki.apache.org/confluence/display/KAFKA/KIP-345%3A+Introduce+static+membership+protocol+to+reduce+consumer+rebalances)
- [Apache Kafka Rebalance Protocol, or the magic behind your streams applications](https://medium.com/streamthoughts/apache-kafka-rebalance-protocol-or-the-magic-behind-your-streams-applications-e94baf68e4f2)
- [Apache Kafka Rebalance Protocol for the Cloud: Static Membership](https://www.confluent.io/blog/kafka-rebalance-protocol-static-membership/)
