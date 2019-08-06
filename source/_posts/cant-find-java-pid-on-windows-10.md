---
title: 解决windows 10下java应用找不到pid
date: 2019-07-05 11:22:11
tags: [jvm, 故障案例]
categories: jvm
keywords: [java.io.tmpdir windows 10, hsperfdata, arthas, jvm, AppData Local Temp]
description: arthas, jps, jconsole等工具会从hsperfdata获取已经启动的java应用信息。如果对应的目录没有访问权限，就会找不到对应的pid。目录路径在临时目录java.io.tmpdir下面的hsperfdata_%USER%，Windows 10默认用户没有读写权限。Windows 10默认临时目录<user>\AppData\Local\Temp\
---

# 问题描述

在Windows 10系统，之前写了 [使用arthas直接操作redis](https://ycwu314.github.io/p/use-arthas-to-operate-redis-direclty.html) 遇到一个问题：
```
λ java -jar arthas-boot.jar
[INFO] arthas-boot version: 3.1.1
[INFO] Can not find java process. Try to pass <pid> in command line.
Please select an available pid.
```
arthas找不到java应用的pid。换jps同样也没有找到。
```
λ jps

```

# 关于hsperfdata

hsperfdata是jvm应用每次运行时记录的性能监控数据。默认在java的临时目录创建。arthas、jps、jconsole等应用，会从hsperfdata目录获取java pid。

arthas找不到java pid，可能的原因有：
1. hsperfdata被禁止。hsperfdata由jvm参数`-XX:+UsePerfData `控制，默认情况是是打开的。
2. 没有权限创建hsperfdata目录。hsperfdata目录默认在java的临时目录创建，名字为`hsperfdata_<username>`
3. 当前用户在hsperfdata目录没有访问权限，不能读写数据。

很有可能是没有hsperfdata目录或者没有访问权限。

# 解决

先找到java的临时目录。java的临时目录由jvm参数`java.io.tmpdir`控制。
```java
System.out.println(System.getProperty("java.io.tmpdir"));
```

在我的电脑上显示结果是
```
C:\Users\ycwu\AppData\Local\Temp\
```
账号是ycwu，对应的hsperfdata目录是hsperfdata_ycwu。打开目录发现有这个文件夹。

右键查看属性
{% asset_img hsperfdata_ycwu属性.png %}

没有用户ycwu的访问权限。。。点击`编辑`->`添加...`，输入用户名，然后`检查名称`
{% asset_img 添加用户.png %}

确定之后，选择`完全控制`
{% asset_img 完全控制.png %}

保存后再次运行java应用，hsperfdata目录下面创建了pid文件。arthas也能找到java pid了。

ps. linux系统的hsperfdata默认是在`/tmp/hsperfdata_<user>`

# 小结

Windows 10的`java.io.tmpdir`里的`hsperfdata`目录默认访问权限有问题，导致jps等工具找不到Java pid。手动设置一下就好了。
