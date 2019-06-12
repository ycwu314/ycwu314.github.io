---
title: SD项目：使用arthas排查问题的经历
date: 2019-06-04 12:08:22
tags: [arthas, java, 故障案例, SD项目]
categories: SD项目
keywords: [arthas, 状态机, 故障案例]
---

# 业务背景简介

核心的房间语音游戏业务，使用事件驱动+状态机轮转设计。
一个event包含房间号、当前轮次、当前游戏状态、期望转入状态等metadata。
使用RocketMQ作为事件源，业务收到mq消息后，根据metadata去初始化状态机对象，再由状态机去执行业务逻辑。

# 问题描述

测试人员反映，test环境的房间服务偶发性卡顿，但是等待一会，又自动恢复，状态机继续轮转。
半天内发生多次，但是不能稳定复现。

# 故障排查思路

状态机不能轮转，最有可能出问题的地方:
1. 没有收到mq消息
2. 收到mq消息，但是业务action处理很久

<!-- more -->

## 排查RocketMQ

test环境的RocketMQ资源是共享的，偶尔会抽风，先排查RMQ的问题。
对于第1点，很好排查。
1. 在mq控制台，确认这段时间没有消息堆积。消息是正常下发的。
2. 收到mq消息，都会打印一条日志
```java
logger.info("receive msg={}", msg);
```
根据mq的接收日志分析，消息正常收到，并且进行了处理。
因此排除是mq中间件的问题。

## 排查业务action

根据日志，有异常的环节是新一轮开始，包括初始化该轮游戏数据、下发歌曲、切换状态、注册超时事件等操作。都在PlaySongAction类处理，先缩小排查范围。
另外，每次卡顿，**大概10分钟就自动恢复**。

PlaySongAction的日志就只有一行
```java
INFO [ConsumeMessageThread_x] PlaySongAction enter play_song[roomId={}, currentRound={}, currentTurn={}, roomState={}, singerId={}] 
```
不足以排查问题。


PlaySongAction类是fali-safe设计
```java
try{
	// business logic
}catch(Exception e){
	logger.error("error, RoomContext=[" + roomContext + "], " e)
	// more code for generic error handling
}
```
如果发生一般异常（除了是抛出Throwable，概率很小），一定会捕获到，并且打印日志。但是error日志并没有。
因此猜测是长时间执行，方法没有返回。

方法执行时间长，常见的原因：
1. 有大量耗时运算
2. 等待IO资源
3. 等待锁
4. 等待其他服务、中间件的返回
5. 遇上gc stw
6. 其他待补充

代码review，没有复杂的计算，没有显式使用锁，没有大量写磁盘的操作。
在监控看这段时间的load、cpu、io和平常基本一样，没有特别可疑。
gc问题可以直接不考虑。

再把范围缩小，猜测是对于其他服务的访问慢造成的。
PlaySongAction访问了mysql、redis、ElasticSearch等中间件，还有其他服务提供的http接口，看来只能逐个排查。

这时候测试同事说又出现卡顿情况。
赶紧`jstack -l <pid> | grep ConsumeMessageThread_`，可是没有看到block之类的提示。
因为不能稳定复现，机会难得，来不及增加debug日志，赶紧用arthas看看。

# 使用arthas排查问题

根据roomId和currentTurn，定位到发生卡顿的日志
```java
INFO [ConsumeMessageThread_3] PlaySongAction enter play_song[roomId={}, currentRound={}, currentTurn={}, roomState={}, singerId={}] 
```

mq worker线程ConsumeMessageThread_3接收了消息，并且进行处理。


使用thread命令找到线程ConsumeMessageThread_3对应的thread ID
```
$ thread 
Threads Total: 32, NEW: 0, RUNNABLE: 13, BLOCKED: 0, WAITING: 15, TIMED_WAITING: 4, TERMINATED: 0                                                                                            
ID              NAME                                           GROUP                           PRIORITY       STATE           %CPU            TIME            INTERRUPTED    DAEMON          
44              as-command-execute-daemon                      system                          10             RUNNABLE        87              0:0             false          true            
41              nioEventLoopGroup-2-3                          system                          10             RUNNABLE        12              0:0             false          false           
32              AsyncAppender-Worker-arthas-cache.result.Async system                          9              WAITING         0               0:0             false          true            
30              Attach Listener                                system                          9              RUNNABLE        0               0:0             false          true            
11              Catalina-utility-1                             main                            1              TIMED_WAITING   0               0:3             false          false           
// 以下省略
```

`thread <thread ID>`看当前线程的调用栈
```java
$ thread 310
"ConsumeMessageThread_3" Id=310 RUNNABLE (in native)
    at java.net.SocketInputStream.socketRead0(Native Method)
    at java.net.SocketInputStream.socketRead(SocketInputStream.java:116)
    at java.net.SocketInputStream.read(SocketInputStream.java:171)
    at java.net.SocketInputStream.read(SocketInputStream.java:141)
    at org.apache.http.impl.io.SessionInputBufferImpl.streamRead(SessionInputBufferImpl.java:137)
    at org.apache.http.impl.io.SessionInputBufferImpl.fillBuffer(SessionInputBufferImpl.java:153)
    at org.apache.http.impl.io.SessionInputBufferImpl.readLine(SessionInputBufferImpl.java:282)
    at org.apache.http.impl.conn.DefaultHttpResponseParser.parseHead(DefaultHttpResponseParser.java:138)
    at org.apache.http.impl.conn.DefaultHttpResponseParser.parseHead(DefaultHttpResponseParser.java:56)
    at org.apache.http.impl.io.AbstractMessageParser.parse(AbstractMessageParser.java:259)
    at org.apache.http.impl.DefaultBHttpClientConnection.receiveResponseHeader(DefaultBHttpClientConnection.java:163)
    at org.apache.http.impl.conn.CPoolProxy.receiveResponseHeader(CPoolProxy.java:165)
    at org.apache.http.protocol.HttpRequestExecutor.doReceiveResponse(HttpRequestExecutor.java:273)
    at org.apache.http.protocol.HttpRequestExecutor.execute(HttpRequestExecutor.java:125)
    at org.apache.http.impl.execchain.MainClientExec.execute(MainClientExec.java:272)
    at org.apache.http.impl.execchain.ProtocolExec.execute(ProtocolExec.java:185)
    at org.apache.http.impl.execchain.RetryExec.execute(RetryExec.java:89)
    at org.apache.http.impl.execchain.RedirectExec.execute(RedirectExec.java:110)
    at org.apache.http.impl.client.InternalHttpClient.doExecute(InternalHttpClient.java:185)
    at org.apache.http.impl.client.CloseableHttpClient.execute(CloseableHttpClient.java:83)
    at org.apache.http.impl.client.CloseableHttpClient.execute(CloseableHttpClient.java:108)
//  此处打码
    at ***************************.service.zsearch.ZSHttpClient.post(ZSHttpClient.java:131)	
//  以下省略

    Number of locked synchronizers = 1
    - java.util.concurrent.ThreadPoolExecutor$Worker@607eb62
```

ZSHttpClient是我们封装的服务，底层使用httpclient，访问ElasticSearch。这里要获取歌曲、专辑、以及人工运营的元数据，组装下发。
从调用栈看，线程等待`java.net.SocketInputStream.socketRead0(Native Method)`的返回。

httpclient底层使用BIO访问网络。如果没有返回，会一直等待。
但是，**祖传的** ZSHttpClient，不可能没有访问超时配置，test环境10秒read timeout超时失败。
看起来是超时配置没有生效。google一下，说是socketRead0的实现有可能导致超时设置无效 [How to prevent hangs on SocketInputStream.socketRead0 in Java?](https://stackoverflow.com/questions/28785085/how-to-prevent-hangs-on-socketinputstream-socketread0-in-java)。

既然是访问ElasticSearch的问题，顺便问了负责运维的同事，这2天刚好在做迁移和扩容ElasticSearch，确实有间歇性服务不稳定。

梳理一下
- ES迁移和扩容，导致服务不稳定
- httpclient使用BIO访问网络，socketRead0的实现可能触发超时无效一直等待的bug

好像说得过去哦。。。但是，
- socketRead0的case应该very rare，一个早上出现多次，说不过去
- **出问题的总是ZSHttpClient.post()方法**，ZSHttpClient.get()方法没有报告异常，从概率来说，有点说不通

于是打开ZSHttpClient.post()的代码，**没有设置SocketTimeout**，但是get()方法是有的。

再次梳理
- ES迁移和扩容，导致服务不稳定
- ZSHttpClient.post()没有设置SocketTimeout，一直等待
- ConsumeMessageThread_3线程等待ZSHttpClient.post()返回
- 于是房间卡顿

这就合理多了。
还有一个疑问，**为什么固定10分钟后又会自动轮转呢**？
猜测是中间网络设备的空闲超时reset，导致socketRead0()返回。
于是去查找ZSHttpClient.post()的error日志，果然在发生卡顿之后的10min，有网络异常日志。ZSHttpClient直接捕获了异常并且返回null，上层调用方PlaySongAction继续执行，由于有null判断，导致PlaySongAction不会出错，但是下发的歌曲数据是有问题的（有日志验证）。

# 故障过程还原

- ES迁移和扩容，导致服务不稳定
- ZSHttpClient.post()没有设置SocketTimeout，一直等待
- ConsumeMessageThread_3线程等待ZSHttpClient.post()返回，效果是线程hang住
- 于是房间卡顿
- 中间网络设备的空闲超时reset，导致socketRead0返回。
- ZSHttpClient.post()捕捉了异常返回null，PlaySongAction继续执行，由于有null判断，不会报错，但是下发错误的歌曲信息，并且进入轮转

# 解决问题

1. fix ZSHttpClient.post()，增加超时配置
```java
RequestConfig requestConfig = RequestConfig.custom()
    .setConnectionRequestTimeout(CONNECTION_TIMEOUT_MS)
    .setConnectTimeout(CONNECTION_TIMEOUT_MS)
    .setSocketTimeout(CONNECTION_TIMEOUT_MS)
    .build();

HttpPost httpPost = new HttpPost(URL);
httpPost.setConfig(requestConfig);
```

2. 访问ElasticSearch的代码监控打点不完善，增加新打点。
3. PlaySongAction对于null的歌曲信息，增加一个日志打点。

验证通过。

# 思考

1. 祖传代码分分钟有惊喜，要有怀疑精神。
2. 根据已有日志，先缩小范围，做出假设，收集证据，验证。
3. 对于不能稳定重现的情况，保留现场（thread dump，heap dump等）很关键。
4. arthas查看线程stack很方便。如果不是使用arthas，那么要逐个排查PlaySongAction访问的服务、中间件，相当费时费力。
5. 不要轻易拍结论，多反问几次。如果随便用socketRead0()和ES迁移搪塞过去，就发现不了ZSHttpClient.post()的问题了。

