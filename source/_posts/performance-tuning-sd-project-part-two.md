---
title: SD项目：高并发的性能优化，part 2
date: 2019-06-11 22:43:41
tags: [java, 性能调优, SD项目, 高并发]
categories:  SD项目
keywords: [性能调优, 高并发, 缓存优化]
---

总结SD项目的性能优化过程和思考，part 2。

往期文章
- {% post_link performance-tuning-sd-project-part-one %}

# 加入游戏房间

用户加入某个游戏房间，成功后会向房间内所有人发送信令通知，“xxx加入房间”。
目前有2种模式的房间，一是小房间（10人以下），二是大房间（up to 1000人）。

## 优化前

单压：
1. 10000+并发加入**不同的小房间**，RT < 400ms。
2. 1000+并发加入**同一个大房间**，RT > 10000+ms。**客户端显示卡顿、甚至崩溃**。测量出客户端能够正常处理的、最大并发加入信令大概在50左右。**redis tps告警**。
<!-- more -->
## 分析&解决

房间允许人数，是一个房间的最大并发度。

客户端收到加入房间成功的信令后，要更新、渲染多个组件。现有服务器端逻辑是，每个成功加入都下发一个单独的信令。1000+并发情况下，客户端瞬间被信令轰炸，进行组件渲染，消耗大量的cpu、内存资源，引发了卡顿、崩溃。

解决的思路是，减少下发信令的个数。
- 交互协议升级，支持一次返回多个成功加入房间的用户信息。
- 延迟下发。相同的房间id，合并一秒内的成功加入请求，再统一下发。

<!-- more -->

加入房间的请求会分散到不同的服务器端实例。合并请求的时候要考虑高可用问题，其中一个解法是：
- 以room_id作为key，获取redis lock，锁定一秒
- 如果获取成功，则发送一条延迟mq，时间为一秒

另外，**考虑保护db资源，给join接口限流，分为单个房间（其实就是处理大房间）和整体接口的级别**。

通过减少信令下发，RT也降下来，redis告警消失。至于redis告警的深层次原因，会在后面讨论。

## 数据对比

优化后：1000+并发加入大房间，客户端每1s只接受一条加入信令，不会崩溃。TP99 < 200ms。redis tps告警消失。

## 思考

1. 量变到质变。原来只有小房间模式，因此单个房间不会产生高并发。客户端可以顺利处理每条信令。但是随着大房间模式的出现，情况就不同了。架构设计也随之升级。
2. 好的测试方案不但测试单个接口，还要验证整个链路。
3. 高并发下要考虑对敏感资源的保护，避免单个接口搞垮系统。

# 房间内点赞功能

对正在演唱的人点赞:
- 一轮有1次给他人点赞机会
- 点赞数每到达一定阈值，延长当前的表演时间，最多延长X秒
- 房间内收到的点赞数会同步到个人页的点赞计数（通过mq异步消费）
- 向客户端发送xx收到点赞信令

## 优化前

单压：2000+ tps，点赞接口RT > 10000ms。客户端卡顿、崩溃。状态机轮转卡顿。**redis tps告警**。

## 解决：客户端崩溃

同最初的加入房间一样，服务器端处理一个点赞后立即发送信令，导致客户端被轰炸。
但是不能直接使用延迟mq消息简单解决，因为“点赞数到达一定阈值，延长当前的表演时间”。为了减少下发的信令数量，并且尽可能兼容中间丢失信令的情况，这个延长时间标记是挂在点赞信令一起下发的，对应的结构体示意：
```json
{
"like": 23,		// 当前点赞数
"extra": 10		// 总的延长表演时间
}
```
如果一刀切所有点赞信令延迟1s合并发送，在边界条件下，会导致延长时间标记不能及时发送，表演时间少了。

解决方法
- 每次触发延长时间，就立即发送该点赞信令。否则延迟1s发送。

效果
- 消灭了信令轰炸。客户端不崩溃了。

redis tps告警会在后面讨论。

## 解决：状态机问题

状态机轮转依靠mq消息触发。如果产生消息堆积，那么状态机就会卡顿。在RocketMQ控制台确认有大量消息堆积，发现是点赞消息。

点赞的伪代码
```java
// 前置检查

// 同步点赞数到个人页。发送mq，消费者异步消费，存储到ES
IncrLikeMsg msg = new IncrLikeMsg();
msg.setUserId("xxx");
msg.setCount(1);
mqService.sendIncrLikeMsg(msg);

// 其他发送信令相关
```

问题在于发送点赞消息的topic，跟状态机轮转是同一个topic！
为什么两个不同类型的消息，使用同一个topic？因为最初不想申请太多的topic，直接用同一个topic，业务在消息体定义event字段区分。
高并发下对同一个人点赞，消费者落盘到ES慢，造成大量点赞msg堆积，影响了状态机轮转msg的消费。

解决：为点赞消息申请一个新的topic。

## 数据对比

优化后：2000+ tps，TP99 < 10ms。**redis tps告警消失**。

## 思考

topic使用要规范，切记偷懒。


# 发送信令接口

上面2个接口都有一个共同情况，大房间+高并发请求，如果瞬间发送大量信令，RT很大，并且redis告警。
使用arthas trace命令，很容易就定位了发送信令接口存在性能问题。

发送信令接口，首先拼装接收人列表，伪代码如下
```java
List<String> userIdList = roomService.getAllUserIdByRoomId(roomId);	      // redis
List<ParticipantVo> participantList = new ArrayList();
for (String userId : userIdList ){
	UserInfo userInfo = userService.getUserInfo(userId)                   // redis
	Long like = redisService.get(getUserLikeKey(userId));                 // redis
	String benifitTag = redisService.get(getUserBenifitKey(userId));      // redis
	String visitorTag = redisService.get(getVisitorKey(roomId, userId));  // redis
	// more code on assembly participantList 
}

// sort participantList by like count desc
// more other codes
```

大量依赖redis。对于1000人的大房间，1000 tps请求，对redis的tps 压力大概是`1000 * 1000 * 3 = 3000000`。redis不跪才怪。

## 点赞数like

只能从缓存获取。但是用sorted set保存点赞数，memeber是userId，score是点赞数。直接`zrevrangebyscorewithscores`一次性读取。1000个member的key算是大key，后续有必要再hash拆分为多个，但是sorted set的特性就消失了。

从sorted set获取点赞数后，还可以省略最后对participantList排序。

## 用户权益benifitTag

用户获得成就之后，得到一个权益标记，有效期一星期，做特殊展示效果。
因为是一星期有效，并且人数有限，使用**vm缓存 + 过期时间**可以解决，不需要每次从redis读取。

## 游客标记vistorTag

只有小房间才有游客标记概念。大房间不需要读取这个标记。直接省略。

## 用户信息UserInfo

UserInfo包含昵称、头像、设备信息。由用户服务维护，底层用redis缓存。
用户信息更新不频繁，可以使用jvm缓存，使用guava cache保存，LRU，目前保留X个，有效期1小时。

## 本地jvm缓存预热的思考

因为请求分散到N个容器，缓存预热发生在N个容器。一个用户要经历N个请求之后，才有可在能所有容器预热用户信息。
即使不是所有容器预热，正常用户的操作，也能够预热一部分容器，从而减少redis压力。

如果容器重启了，jvm缓存就会丢失，目前避免在业务高峰尤其是大房间开始前重启就可以了。

## 数据对比

优化后，单压发送信令接口，1000人大房间，1000+ tps，TP99 < 10ms。redis tps告警消失。

