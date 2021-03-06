---
title: sql性能优化case 2
date: 2020-04-05 19:13:21
tags: [sql, 性能优化]
categories: [sql]
keywords: [sql 调优]
description: 一次sql优化经历。
---

# 背景

设备管理页面支持对摄像头、WiFi、电子围栏等设备进行管理。现场投诉打开很慢。
不管是几十万、还是几千的接入设备类型，都慢成狗。
<!-- more -->

# 优化过程

首先观察现状：
- 页面上可以选择不同的设备类型进行操作。
- 不同设备类型的数据不一样，有的几十万，有的几千条。
- 但是即使选择接入数量少的设备类型，接口返回都非常缓慢。

打开接口，发现每次查询都从一个视图捞取数据：
```sql
select * from vw_devices
where device_type = 'xxx' // 设备类型
```

打开`vw_devices`视图一看，震惊了：
```sql
select id, 'camera' as device_type, // 省略一堆属性，把个别属性转换
from camera
UNION ALL
select id, 'wifi' as device_type, // 省略一堆属性，把个别属性转换
from wifi
UNION ALL
// 省略多个类型的设备表
```

这个视图暴露了两个问题：
- 操作一个类型的设备，却硬生生要`UNION ALL`读取其他不相关的设备类型数据。不慢才怪。
- 这个视图是为了上层应用写的方便，把不同类型的设备进行抽象。

根本问题是最初设计，前人对设备的抽象不够。
摄像头、wifi的属性肯定不太一样。但是都可以进行抽象，比如id、设备类型、标准编码等。这些记录在主表。
不同类型设备的个性化属性记录在各自的扩展表。
其实就是面向对象设计、抽取领域模型。

扯远了。要重新设计抽象套回去，牵连太多，只能就着现状修改：
- 原来对不同设备`UNION ALL`的视图不能再使用了。
- 应用层根据不同设备，直接读取不同的设备表。

# 小结

解决这个慢查询问题很简单。但是背后隐藏的是领域理解不深才是大问题😥。
