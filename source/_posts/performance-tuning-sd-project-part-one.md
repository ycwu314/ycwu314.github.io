---
title: SD项目：性能优化，part 1
date: 2019-06-07 21:30:07
tags: [java, 性能调优, SD项目]
categories: SD项目
keywords: [java, 性能调优]
---

总结SD项目的性能优化过程和思考，part one。

# 背景说明

使用预发布环境进行压测，只部署一个容器，容器配置和生产环境一致。
压测包含单压（同一时间只压测一个接口）和混压（同一时间压测多个接口，模拟用户真实使用操作）。
压测对象是房间服务。

# 首页在线人数

打开app，首页右上角显示当前在线人数“xxx 人在等你”。

## 优化前

在线人数由一个redis key存储。后端读取redis直接返回。
在高并发的情况下，就是典型的热点redis key问题，直接拖慢这个key所在的redis实例。

## 解决

对于数据一致性不高的场景，热点key容易解决，最简单的是增加本地jvm缓存，再由定时任务更新数据。也可以使用guava cache来实现。

## 数据对比

优化前：5w并发，RT 180+ms
优化后：0ms

## 思考

为什么要显示实时的在线人数呢？这是一开始我就argue的地方，这是赤果果地向竞品暴露我方产品情况。。。
ps. 后续产品展示终于改为区间显示，99+，999+，9999+等。

<!-- more -->

# 日志堆栈丢失

## 优化前 

后端日志通常是这样输出，包含异常堆栈
```java
logger.error("error: ", e);
```

但是，混合压测（后续简称“混压”）的时候，日志文件开始出现大量异常，却没有调用堆栈，不知道报错的地方。
```java
java.lang.NullPointerException

java.lang.IllegalArgumentException
```


## 解决

dump stack trace是一个耗时操作。jvm默认做了性能优化，对于反复抛出的异常，生成一个不包含stack trace的异常返回。
对应的开关参数是`OmitStackTraceInFastThrow`，默认开启。在测试环境把这个特性关闭：

```
-XX:-OmitStackTraceInFastThrow
```

参见 [Release Note](https://www.oracle.com/technetwork/java/javase/relnotes-139183.html#vm)

>The compiler in the server VM now provides correct stack backtraces for all "cold" built-in exceptions. For performance purposes, when such an exception is thrown a few times, the method may be recompiled. After recompilation, the compiler may choose a faster tactic using preallocated exceptions that do not provide a stack trace. To disable completely the use of preallocated exceptions, use this new flag:  -XX:-OmitStackTraceInFastThrow.

之后堆栈都正常打印。fix了几个边界情况的NPE、类型判断的问题。

## 思考

真是活久见。平时遇到`OmitStackTraceInFastThrow`的情况比较少，想了一会才想起这个参数。平常的知识储备还是很重要的。


# 首页推荐歌曲片段列表

![首页推荐歌曲片段](https://s2.ax1x.com/2019/06/08/VDf4IJ.png)

展示歌曲列表，用户可以试唱。

流程：
1. 从推荐服务捞取歌曲片段id列表
2. 从ES获取歌曲片段元数据，领唱人数据等
3. 从用户服务获取领唱人头像、昵称
4. 从交互服务获取点赞、收藏信息
5. 组装下发

## 优化前

1W并发，直接跪了，RT > 10000ms。

## 解决

一个接口包含多个服务调用，要看瓶颈在哪里，最直接的方式是每个调用前、后加上打点代码，打印调用时间。
不过有了arthas，一切就简单多了。

```
# trace -n 3 com.xxx.SoloService recommendAlbum '#cost > 1000'
```
参数的含义:
- -n: 跟踪次数
- com.xxx.SoloService: 包名+类名
- recommendAlbum: 方法名
- '#cost > 1000' : 过滤表达式，只跟踪cost大于1000ms的请求

完整的调用栈很长，当时也没有留下截图，这里粘贴arthas官网的例子输出
```
`---ts=2018-12-04 01:12:02;thread_name=main;id=1;is_daemon=false;priority=5;TCCL=sun.misc.Launcher$AppClassLoader@3d4eac69
    `---[12.033735ms] demo.MathGame:run()
        +---[0.006783ms] java.util.Random:nextInt()
        +---[11.852594ms] demo.MathGame:primeFactors()
        `---[0.05447ms] demo.MathGame:print()
```

具体使用参见 [arthas的trace文档](https://alibaba.github.io/arthas/trace.html?highlight=trace)

tips:
- trace每次只能跟踪一级方法的调用链路。
- 记得加上-n参数，限制跟踪次数，否则压测场景下很容易OOM。

有了arthas这个好使的工具，剩下的就是体力活了。

1. 推荐服务
首先跪的，RT > 10000ms。增加redis，避免直接从ES拉取计算数据。
优化效果：推荐RT 50-200ms。

2. 接着跪的是查询歌曲元数据。耗时集中在等待ES返回。
```java
// segment是片段
for(String segmentId : segmentIdList){
	// read from ES
}
```
step1，片段数据变更不频繁，适合放入缓存，以片段id作为key，expire 1800s。
片段id比较充分打散，读写压力均摊到redis cluster多个分片，暂时不考虑jvm缓存。
step2，for循环串行查询片段数据，改为java8的`parallelStream`并发查询。
优化效果：全部命中缓存RT < 10ms，全部不命中缓存RT < 500ms。

3. 用户服务
原先每个片段单独查询用户信息，改为一次批量查询。
优化效果：优化前RT 30-100ms，优化后RT 5-10ms。

4. 交互服务
优化前每个片段单独查询一次点赞状态，改为新增一个批量查询接口。
优化效果：优化前总交互服务查询耗时1000+ms，优化后50-100ms。

## 数据对比

优化后：10W并发查询，接口整体rt 200-1000ms。

## 思考

1. 从领域模型角度，个人推荐歌曲片段功能，不应该划分在房间服务，后续要单独拆分。
2. 复杂接口的性能优化套路：
- 使用arthas trace，找到核心调用链的耗时分布，确定优化的对象。
- 增加缓存、多个单次查询变为一次批量查询、多个单次查询改为并发查询等手段。

# 推荐在线用户

![推荐用户列表](https://s2.ax1x.com/2019/06/08/VDhAeS.png)

## 优化前

3W并发，RT 5000+ms

## 解决

优化思路同“首页推荐歌曲片段列表”，在此不再重复。

## 数据对比

优化后：10W并发，RT 100ms。


# 房间列表接口

显示当前有效的N个游戏房间，返回房间状态、房主信息、人数、歌单等。

这个接口的逻辑流程：
1. 从room_info表过滤房间状态、创建时间，得到房间id列表
2. 从participant表得到房间人数
3. 调用其他接口获取房主的个人信息

直接落盘查询数据库，在高并发下是肯定会直接跪了，因此v1.0的实现是带有缓存，更新时间15-30s，由后台任务刷新。
但是产品认为体验不好，创建房间怎么没有立即显示，blablabla，被迫改先为直接查询数据库（v1.5）。由于对查询条件建立相关索引，因此也不会慢到哪里去，可以撑一段时间。

v2.0设计思路是房间列表直接从缓存数据构建，从新建房间、销毁房间、加入房间、退出房间、房间状态变化等等，全部直接操作缓存，牵涉改造点多（10+接口），暂时没有排上日程。

## 优化前

单压：1W并发查询房间列表，RT 3000+ms。
混压：1W并发查询房间列表 + 1000并发创建房间，RT 15000+ms。触发数据库中间件慢查询警告。

## 解决

从数据库控制台发现慢查询语句，伪代码如下
```sql
select count(1) from participant
where room_id = xxx
```
participant表根据room_id字段分库，并且建立索引。

但是单压查询性能去到3000+ms，说不过去。
第一感觉是没有索引，或者索引没有生效：
1. 在数据库检查，真的没有索引。。。
2. 接着排查代码git历史，有增加索引的commit。

最后定位是几个月前部署单的问题，导致线上没有索引，因此查询是full table scan，并且当前分表数据10W+行，慢是理所当然。

sql慢查询不仅影响单个接口性能，高并发情况下对系统整体危害很大：
1. 从connection pool获取一个connection，执sql，因为执行的慢，该connection没有立即返回，新的请求只能从连接池获取/创建connection来执行。
2. 高并发场景，重复1)
3. 本地连接池打爆
4. 因为是多个app实例，接着打爆数据库连接数
5. 其他接口涉及访问db的接口也跪了

加上索引后，1W并发查询，RT从3000+ms降到100ms。
这时候再向产品argue，就允许了10s的缓存。

## 数据对比

优化后：（增加索引、定时任务和10s jvm缓存）10w并发，RT < 30ms。
消灭了数据库的慢查询。

## 思考

1. 数据库部署单漏掉建立索引，这个失误有点低级。值得考虑的是，人工操作容易失误，也没有相应的部署后检查步骤，**流程有提升空间**。
2. trade off。 用户对一个列表数据的实时性有多敏感？产品的角度，理所当然觉得一切都是实时性就是最好。但是工程角度，要考时间限制（一个迭代有好多需求呢），方案复杂度，产出投入比（做了很多，但用户可能根本不care）。
**做架构设计和实现，要明白约束条件，权衡的利弊，产出投入比，将来升级要改动的地方**。

# 大量日志文件导致磁盘告警

压测半天过去，收到磁盘空间使用率80%的告警。

## 优化前

容器分配了50GB磁盘，logs已经使用了40+GB。
以当前并发量的磁盘消耗速率来计算，线上环境也就只撑不过2天（因为有多个容器分摊）。

## 解决

首先，分析后端都写了哪些日志文件：
- access log。spring boot内嵌的tomcat写的access log。一个请求写入<1KB，方便排查问题，不需要找运维查询前置的Nginx查询访问日志，保留。
- ElasticSearch操作日志。占用了将近30GB，每次查询都把返回body打印，相当大。
- application日志。包括接收mq日志、房间轮转日志、信令发送日志、用户操作日志等，占用了 6+ GB。
- error日志。主要是异常堆栈，占用了5+GB。

分析完毕，先手动清理了日志文件，防止写爆磁盘。接下来逐个处理。

### ElasticSearch操作日志

显然大头在ElasticSearch操作日志。最直接是修改日志级别，只在debug级别才输出ES日志。
但是有另一个权衡点，ES的底层数据主要由爬虫系统、运营管理系统写入和修改，房间服务只是做消费。目前系统还在快速迭代，发生过写入个别脏数据导致房间消费失败。为了避免扯皮，还是尽量保留每个请求的响应数据。

思考：各个服务直接对接存储层，并且是schema free，没少踩坑。如果抽取歌单服务，修改限制在一个服务，那么会有改善。但是目前人力不足，暂时不考虑。

于是采取折中方案，依然保留ES的响应输出，但是修改loggback配置
```xml
<appender name="ROLLING" class="ch.qos.logback.core.rolling.RollingFileAppender">
  <file>es.txt</file>
  <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
    <!-- rollover daily -->
    <fileNamePattern>es-%d{yyyy-MM-dd}.%i.txt.gz</fileNamePattern>
     <!-- each file should be at most 100MB, keep 60 days worth of history, but at most 20GB -->
     <maxFileSize>200MB</maxFileSize>    
     <maxHistory>4</maxHistory>
     <totalSizeCap>20GB</totalSizeCap>
  </rollingPolicy>

  <!-- 其余配置省略  -->
</appender>
```

1. logback是支持文件压缩的，`fileNamePattern`增加gz后缀就可以自动压缩为gz文件。对于纯文本压缩，通常可以达到10:1或者更高的压缩比例。
2. 只保留最近4天的日志。

当然，这样的缺点是排查问题可能要先解压缩日志文件，不过问题不大。

### application日志

application日志比较杂乱，多种类型日志穿插，输出混乱，正好做梳理和拆分。
1. 发送信令日志signal，记录了发送什么信令、向哪些客户端发送、是否成功，是排查"服务器端有无正常发出信令"、"客户端有无收到信令"这2个核心问题的基础。不能省去。直接用另一个logger配置写到其他文件，加上压缩和滚动配置。
2. mq接收日志。接收后打印消息体。由于房间的核心是轮转由mq消息触发，mq日志能够排查房间不轮转问题。拆分出来。
3. 房间服务日志room。这是核心部分。存在问题：
- 之前迭代输出调试日志，已经没用，可以删掉
- 啰嗦的、不能帮助排查问题的无效日志信息，删掉
- 规范化INFO日志内容。统一房间服务的上下文RoomContext输出的字段，方便grep查询


### error日志

首先，我们封装了业务相关的BizException。很多BizException不需要堆栈，只需要当前上下文信息就可以。
举个例子，用户加入房间失败。只需要输出一行日志就足够排查问题
```java
userId={},action=JOIN,roomId={},currentRound={},currentTurn={},reason=ROOM_FULL
```
如果打印完整堆栈，通常有20到50行。

## 数据对比

优化之后，在相同压测压力之下，每小时消耗磁盘空间节省80-90%左右。
application日志输出更加清晰。
error日志减少无用堆栈，空间节省90-95%。


## 思考

后续日志优化
- 目前mq日志、房间操作日志、房间状态机日志、房间信令日志分散，可以考虑根据roomId进行日志归集优化。
- 结合Diamond做动态日志级别调整。

另外，对线上环境配置做了优化：
1. 默认磁盘空间告警水位线80%，比较高了，调整到60%。
2. 提前扩展线上磁盘容量。

