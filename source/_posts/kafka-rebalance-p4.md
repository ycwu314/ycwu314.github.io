---
title: kafka rebalance系列：incremental cooperative rebalancing
date: 2020-04-21 19:56:41
tags: [kafka]
categories: [kafka]
keywords: [kafka incremental cooperative rebalancing]
description: kafka 2.3 增加了incremental cooperative rebalancing，对大规模消费者集群的重平衡进行优化。
---

# Incremental Cooperative Rebalancing

>The key idea behind all the designs proposed here is to change the assumption we've always made with groups and their resources until now: 
>when you go into a JoinGroup, it is expected that you give up control of all resources that you control and get them into a clean state for handoff. 

在kafka 2.3以前，rebalance对kafka consumer集群性能的影响，体现在一旦进入JoinGroup则立即放弃控制资源，其中涉及状态初始化、offset提交、释放partition，是耗时的操作。
<!-- more -->
KIP-429 这个 KIP 在原有的紧迫再平衡协议（eager rebalance protocol）的基础上，增加了消费者增量平衡协议（Incremental Rebalance Protocol）。
与 eager 协议不同，eager 协议总是在重新平衡之前撤销所有已分配的分区，然后尝试重新分配它们。
而 incremental 协议允许消费者在重新平衡事件期间保留其分区，从而尽量减少消费者组成员之间的分区迁移。因此，通过 scaling out/down 操作触发的端到端重新平衡时间更短，这有利于重量级、有状态的消费者，比如 Kafka Streams 应用程序。


>Incremental because the final desired state of rebalancing is reached in stages. A globally balanced final state does not have to be reached at the end of each round of rebalancing. A small number of consecutive rebalancing rounds can be used in order for the group of Kafka clients to converge to the desired state of balanced resources. In addition, you can configure a grace period to allow a departing member to return and regain its previously assigned resources.

“增量”是指最终平衡状态经历多个阶段实现，而不需要在一次全局stop-the-world平衡中实现。可以设置一个grace period，方便consumer重新加入和再次拿到之前分配的资源。

>Cooperative because each process in the group is asked to voluntarily release resources that need to be redistributed. These resources are then made available for rescheduling given that the client that was asked to release them does so on time.

“协同”是指group内的进程自愿释放需要被重新分发的资源。

Incremental Cooperative Rebalancing 从以下3个方面进行优化：
- Design I: Simple Cooperative Rebalancing
- Design II: Deferred Resolution of Imbalance
- Design III: Incremental Resolution of Imbalance

# Design I: Simple Cooperative Rebalancing

member进程:
- member在JoinGroup中附带订阅的topics，以及分配的partitions列表。
- **在JoinGroup过程中，memeber继续持有已有资源。（对比原来的设计：一旦进入JoinGroup则立即放弃控制资源）**
- 处理assignment中新分配的分区
- **如果assignment包含RevokePartitions，则立即停止处理对应的分区**，commit，并且立即初始化另一轮join group

leader进程：
- 为所有member计算分区；另外，通过member上报的信息，计算RevokePartitions。
- leader要为group内失联的topic partition负责（持有这些分区的member可能不再返回）。解决方式是在上边步骤，分配分区的时候要包含所有分区（而不是只局限于上报的分区）

这一版本的优化只对RevokePartitions发生影响。对比以前的设计，一旦进入JoinGroup，所有consumer都要停止处理、commit offset。

# Design II: Deferred Resolution of Imbalance

>we should schedule another rebalance instead of always trying to resolve imbalance immediately.

在Design 1的基础上，在assignment增加ScheduledRebalanceTimeout，延迟处理不平衡状态。
```
Assignment (Leader → Member):

Assignment => Version AssignedTopicPartitions RevokeTopicPartitions ScheduledRebalanceTimeout
  Version                      => int16
  AssignedTopicPartitions      => [Topic Partitions]
    Topic         => String
    Partitions    => [int32]
  RevokeTopicPartitions        => [Topic Partitions]
    Topic         => String
    Partitions    => [int32]
  ScheduledRebalanceTimeout    => int32
```

新增配置：
- `scheduled.rebalance.max.delay.ms`(默认5min)。对应上面的ScheduledRebalanceTimeout。

member进程：
- 如果`ScheduledRebalanceTimeout > 0`，则在超时之后尽快rejoin（RevokePartitions字段为空才设置该字段）。

>As long as this delay is active, the lost tasks remain unassigned. This gives the departing worker (or its replacement) some time to return to the group. Once that happens, a second rebalance is triggered, but the lost tasks remain unassigned until the scheduled rebalance delay expires.

`scheduled.rebalance.max.delay.ms`允许延迟若干时间才触发rebalance，在这期间部分任务未被分配。离开的worker有机会在这时间内重新加入group。**当超时发生，再触发一次rebalance**。这样设计是期望原来worker能够及时rejoin，再下一次rebalance就不需要revoke partition。

kafka 0.11增加了配置：`group.initial.rebalance.delay.ms`，作用是类似的，但是只应用于空组。ScheduledRebalanceTimeout应用场景更广。

# Design III: Incremental Resolution of Imbalance

在Design 2的基础上，允许leader以多次迭代、每次只重新分配部分分区的方式、实现rebalance。

# 小结

kafka 2.3的增量协同平衡优化：
- member进入JoinGroup状态，继续持有资源。只对RevokePartitions释放资源。
- 对于RevokePartitions，不是立即释放，而是等待`scheduled.rebalance.max.delay.ms`，让离开的worker有机会rejoin。发生超时后再触发rebalance。
- `scheduled.rebalance.max.delay.ms`是`group.initial.rebalance.delay.ms`的升级

# 参考

- [Incremental Cooperative Rebalancing: Support and Policies](https://cwiki.apache.org/confluence/display/KAFKA/Incremental+Cooperative+Rebalancing:+Support+and+Policies)
- [KIP-415: Incremental Cooperative Rebalancing in Kafka Connect](https://cwiki.apache.org/confluence/display/KAFKA/KIP-415%3A+Incremental+Cooperative+Rebalancing+in+Kafka+Connect)
- [Apache Kafka Rebalance Protocol, or the magic behind your streams applications](https://medium.com/streamthoughts/apache-kafka-rebalance-protocol-or-the-magic-behind-your-streams-applications-e94baf68e4f2)

