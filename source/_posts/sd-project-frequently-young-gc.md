---
title: SD项目：频繁young gc的优化
date: 2019-06-14 14:21:16
tags: [java, jvm, SD项目, 高并发, 故障案例]
categories: SD项目
keywords: [高并发, jvm, 垃圾回收, young gc]
description: 压测遇到频繁young gc问题。使用jstat -gcutil查看内存分区使用状况。计算cms收集器新生代大小遇到了问题。扩大新生代空间，减少young gc次数，单次gc耗时增加很少。
---

这次分享SD项目压测过程中遇到的频繁young gc问题。

“高并发的性能优化”的往期文章
- {% post_link performance-tuning-sd-project-part-one %}
- {% post_link performance-tuning-sd-project-part-two %}
- {% post_link performance-tuning-sd-project-part-three %}


# 现状

压测的时候，经常收到gc次数告警。jvm young gc频繁，一分钟大概20次。单次young gc耗时约40ms。Full gc很少发生。使用java8，使用CMS收集器。

# 分析

登入容器，每1s打印应用的jvm使用情况（百分比），原来的截图没有保留，以下是示意图
```
# jstat -gcutil <pid> 1s
  S0     S1     E      O      M     CCS    YGC     YGCT    FGC    FGCT     GCT   
  0.00   0.00  71.73  29.58  95.52  93.03     11    0.114     2    0.273    0.387
```
观察一段时间，发现E（eden）区消耗很快。O（old）区基本不变（记得是20到21）。表明当前新生代的对象绝大部分生存周期都很短，经历young gc就被回收掉。

跟内存分配的jvm参数，只配置了
```
-Xms4096m -Xmx4096m
```
没有指定新生代（-Xmn或者-XX:NewRatio或者-XX:NewSize）。按照，那么默认的新生代大小大约是`4G*(1/(1+2))=1.37G`。Eden区的大小是`1.37G*0.8=1.096G`。 

真的是这样吗？

<!-- more -->

```
# java -server -Xmx4096m -Xms4096m -XX:+PrintGCDetails -XX:+UseConcMarkSweepGC -XX:+UseParNewGC -version

java version "1.8.0_112"
Java(TM) SE Runtime Environment (build 1.8.0_112-b15)
Java HotSpot(TM) 64-Bit Server VM (build 25.112-b15, mixed mode)
Heap
 par new generation   total 613440K, used 32721K [0x00000006c0000000, 0x00000006e9990000, 0x00000006e9990000)
  eden space 545344K,   6% used [0x00000006c0000000, 0x00000006c1ff4420, 0x00000006e1490000)
  from space 68096K,   0% used [0x00000006e1490000, 0x00000006e1490000, 0x00000006e5710000)
  to   space 68096K,   0% used [0x00000006e5710000, 0x00000006e5710000, 0x00000006e9990000)
 concurrent mark-sweep generation total 3512768K, used 0K [0x00000006e9990000, 0x00000007c0000000, 0x00000007c0000000)
 Metaspace       used 2388K, capacity 4480K, committed 4480K, reserved 1056768K
  class space    used 261K, capacity 384K, committed 384K, reserved 1048576K
```
![蘑菇头挠头](http://images.bqshuo.com/0cd32859f4ef4f2d834158729d2cbdb0.jpg)
实际的eden只有545344K，跟原先估算的1.096G，相差将近1半！在这篇文章找到答案：[CMS GC 默认新生代是多大?](https://www.jianshu.com/p/832fc4d4cb53)。

# 解决
手动调整新生代内存大小
```
-Xmn1500m
```
`-Xmn=1500m`效果等价于`-XX:NewSize=1500m -XX:MaxNewSize=1500m`。

再次压测，1分钟young gc次数变为5-6次，单次young gc耗时约42ms。

# more on young gc
为什么新生代扩大为原来的3倍，但是单次gc时间却增加很少呢？
新生代通常使用copy算法，**消耗时间=t(扫描eden)+t(扫描old)+t(复制到survivor)**。
对于jvm来说，扫描速度很快，耗时大的操作是复制对象。扩大eden，触发young gc的间隔变长，对于短生命周期的对象，在更长的时间维度上，可能已经不存活，省去了复制步骤，从而节省时间。所以young gc耗时和新生代大小不是线性关系。

# 思考

纸上得来终觉浅，绝知此事要躬行。搬砖要多动手才容易发现坑。



