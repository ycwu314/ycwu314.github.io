---
title: 使用arthas直接操作redis
date: 2019-07-04 17:50:24
tags: [arthas, java, 故障案例]
categories: 故障案例
keywords: [arthas]
description: 容器化部署和生产环境隔离，不能直接访问中间件数据。使用arthas的tt命令找到一个中间件客户端的实例，然后通过`tt -i <index> -w 'target.xxx()'`直接访问中间件。
---

现在是容器化部署，镜像都是干净的，只有基本的Linux和需要的runtime库，没有安装日常使用的各种中间件客户端，例如redis-cli。
有时候排查问题，需要读取从中间件数据，但是所在容器没有安装中间件的客户端，或者由于网络隔离不能方法问，该怎么办呢？

如果应用有访问中间件的组件，那么可以使用arthas来找到对应组件，然后为所欲为了~下面以访问redis讲解。
<!-- more -->

# 启动arthas

```
wget https://alibaba.github.io/arthas/arthas-boot.jar
java -jar arthas-boot.jar
```

然后选择java应用的pid：
```
[INFO] arthas-boot version: 3.1.1
[INFO] Found existing java process, please choose one and hit RETURN.
* [1]: 10904 com.godzilla.MedicalApplication
  [2]: 9628 org.jetbrains.jps.cmdline.Launcher
1
[INFO] Start download arthas from remote server: https://maven.aliyun.com/repository/public/com/taobao/arthas/arthas-packaging/3.1.1/arthas-packaging-3.1.1-bin.zip
```

## tt

这里要使用tt命令，详见[官网介绍](https://alibaba.github.io/arthas/tt.html)
>方法执行数据的时空隧道，记录下指定方法每次调用的入参和返回信息，并能对这些不同的时间下调用进行观测


```
$ tt -n 3 -t com.godzilla.inquiryassisstant.util.RedisService get
Press Q or Ctrl+C to abort.
Affect(class-cnt:1 , method-cnt:1) cost in 64 ms.
 INDEX   TIMESTAMP            COST(ms)   IS-RET  IS-EXP   OBJECT         CLASS                           METHOD
---------------------------------------------------------------------------------------------------------------------------------------  1001    2019-07-04 18:33:09  13.938899  true    false    0x14496aa8     RedisService                    get
```
命令参数说明：
- -n: 指定记录的次数，防止jvm被撑爆。
- -t: 记录每次的执行情况

后面是类的全路径，以及观察的方法。

在tt所有输出参数中，最重要的是index列，时间片段记录编号，每一个编号代表着一次调用，后续tt还有很多命令都是基于此编号指定记录操作。

选择其中一个index编号，然后使用`-w`参数执行具体的方法。
```s
$ tt -i 1001 -w 'target.get("kkk")'
@String[12345]
Affect(row-cnt:1) cost in 19 ms.
```
其中`target`代表被观察的对象，即要使用的RedisService类。




