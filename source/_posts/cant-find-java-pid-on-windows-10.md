---
title: 解决windows 10下java应用找不到pid
date: 2019-07-05 11:22:11
tags: [jvm, 故障案例]
categories: jvm
keywords: [jvm, hsperfdata, jps, arthas]
description: arthas, jps, jconsole等工具会从hsperfdata获取已经启动的java应用信息。如果对应的目录没有访问权限，就会找不到对应的pid。目录路径在临时目录java.io.tmpdir下面的hsperfdata_%USER%。
---

之前写了 [使用arthas直接操作redis](https://ycwu314.github.io/p/use-arthas-to-operate-redis-direclty.html) 遇到一个问题：
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

-XX:+UsePerfData 

默认情况是是打开的

<!-- more -->

