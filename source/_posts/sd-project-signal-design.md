---
title: SD项目信令设计总结
date: 2019-06-19 10:57:04
tags: [SD项目, 系统设计]
categories: SD项目
keywords: [信令设计, 协议设计]
---

在语音游戏房间，服务器端下发信令，通知客户端房间内状态变化、用户间互动行为。由于当时的接入层对全双工通信支持不友好，并且交互次数和频率相对少，因此客户端向服务器通知的行为采用http接口实现。
下面是信令协议设计的总结。

# 版本号

协议的升级、修改，可能导致旧客户端发生不兼容行为。因此使用版本号区分，客户端只处理自己接受的版本号。

# 信令id

标识一个信令。

# 序号

序号sequenceNo用来表示信令的先后顺序。
根据信令的不同，序号生成算法也不一样。
和状态轮转相关的、房间行为强相关的，采用redis自增，key为房间id，保证序号是单调递增。
其他类型的信令，允许丢失的，例如点赞，则简单使用时间戳。

# 下发时间

服务器下发信令的时间戳。

# 信令分组

type字段用来对信令分组。分组字段可以增加可读性，更重要的是，同一类型的信令，客户端可以指定基础的处理策略。

# 基础信息

每个游戏房间都包含房间号、展示部分用户列表等基础信息。考虑客户端实现的简单和容错性，大部分信令都会携带baseInfo。

# 扩展字段

每个特定信令的扩展数据。比如一个xxx加入房间的信令：
```json
"extra":{
	"userId": "123",
	"name": "",
	"avatar": ""
}
```

# 信令策略

信令下发，有可能乱序，有可能超时，有可能瞬间接收大量信令被轰炸。客户端可以根据信令的分组类型配置通用的信令处理策略，如果有必要，还可以对具体某个信令指定处理策略。
例如，点赞信令属于可以丢弃的操作。如果接收到新的信令，序号比最近处理的要小，则直接丢弃。


