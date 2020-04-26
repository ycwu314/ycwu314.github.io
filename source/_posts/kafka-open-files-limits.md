---
title: kafka：解决too many open files
date: 2020-04-24 11:34:49
tags: [kafka, linux]
categories: [kafka]
keywords: [kafka too many open files]
description: kafka报错too many open files，需要修改ulimit限制。
---

在一台机器上kafka server.log发现一堆"too many open files"异常：
<!-- more -->
```
[2020-04-16 15:20:39,782] ERROR Error while accepting connection (kafka.network.Acceptor)
java.io.IOException: 打开的文件过多
	at sun.nio.ch.ServerSocketChannelImpl.accept0(Native Method)
	at sun.nio.ch.ServerSocketChannelImpl.accept(ServerSocketChannelImpl.java:422)
	at sun.nio.ch.ServerSocketChannelImpl.accept(ServerSocketChannelImpl.java:250)
	at kafka.network.Acceptor.accept(SocketServer.scala:337)
	at kafka.network.Acceptor.run(SocketServer.scala:280)
	at java.lang.Thread.run(Thread.java:745)
```

ps. 关联的WARN日志： 
```
Attempting to send response via channel for which there is no open connection, connection id
```

`ulimit -n`发现openfiles是1024，实在太小了。

解决：
1. 临时修改：`ulimit -n 102400`。重启kafka server。
2. 永久修改`/etc/security/limits.conf`
```
vim /etc/security/limits.conf  
#在最后加入  
kafka soft nofile 102400  
kafka hard nofile 102400  
```

ulimit扩展：
```
-H  ：hard limit ，严格的设定，必定不能超过这个设定的数值
-S  ：soft limit ，警告的设定，可以超过这个设定值，但是若超过则有警告信息
```
