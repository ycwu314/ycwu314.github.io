---
title: redis keyspace 消息通知
date: 2020-01-24 13:35:29
tags: [redis]
categories: [redis]
keywords: [redis keyspace]
description: redis keyspace / keyevent 提供
---

# 前言

redis提供了监听key变更（新增、修改、删除等）通知的能力。通过订阅（subscribe）键空间主题即可。
<!-- more -->
对应有2个主题：
- `__keyspace@database__:KeyPattern`
- `__keyevent@database__:OpsType` 

对于每个修改数据库的操作，键空间通知都会发送两种不同类型的事件消息：keyspace 和 keyevent。以 keyspace 为前缀的频道被称为键空间通知（key-space notification）， 而以 keyevent 为前缀的频道则被称为键事件通知（key-event notification）。

因为 Redis 目前的订阅与发布功能采取的是发送即忘（fire and forget）策略， 所以如果你的程序需要可靠事件通知（reliable notification of events）， 那么目前的键空间通知可能并不适合你：当订阅事件的客户端断线时， 它会丢失所有在断线期间分发给它的事件。并不能确保消息送达。


# 开启配置

键空间通知会带来额外的性能消耗，因此默认是关闭状态。
为了开启键空间通知，需要修改配置文件：
```
notify-keyspace-events "KEA"
```

具体选项有：

| 选项 | 详情 |
| - | --------------------------------------------------------------------- | 
| K | Keyspace events, published with __keyspace@<db>__ prefix.             | 
| E | Keyevent events, published with __keyevent@<db>__ prefix.             | 
| g | Generic commands (non-type specific) like DEL, EXPIRE, RENAME, ...    | 
| $ | String commands                                                       | 
| l | List commands                                                         | 
| s | Set commands                                                          | 
| h | Hash commands                                                         | 
| z | Sorted set commands                                                   | 
| t | Stream commands                                                       | 
| x | Expired events (events generated every time a key expires)            | 
| e | Evicted events (events generated when a key is evicted for maxmemory) | 
| A | Alias for g$lshztxe, so that the "AKE" string means all the events.   | 

K、E必须至少填写一个，否则不生效。
另外，选项要带有双引号，否则不生效。

# 订阅键空间通知

`subscribe` 或者 `psubscribe` (支持模式匹配) 订阅对应话题。

```
127.0.0.1:6379> subscribe __keyspace@0__:xx
Reading messages... (press Ctrl-C to quit)
// 执行订阅命令
1) "subscribe"
2) "__keyspace@0__:xx"
3) (integer) 1

// 以下操作在另一个窗口进行
// set xx 1
1) "message"
2) "__keyspace@0__:xx"
3) "set"

// expire xx 3
1) "message"
2) "__keyspace@0__:xx"
3) "expire"

1) "message"
2) "__keyspace@0__:xx"
3) "expired"
```

# 参考

- [Redis Keyspace Notifications](https://redis.io/topics/notifications)
- [Redis 事件通知（keyspace & keyevent notification）](https://blog.csdn.net/qijiqiguai/article/details/78229111)
