---
title: 记一次运营平台引发的故障
date: 2019-07-15 20:47:48
tags: [SD项目, 故障案例]
categories: [SD项目]
keywords: [故障案例, 运营平台, ElasticSearch]
description: 运营后台为处理一个需求，增加了定时任务，优化不足，结果导致ElasticSearch慢查询，最终影响了正常app业务。良好的测试用例覆盖、常态化性能压测、好的code review以及对需求合理性的推敲，都有助于避免同类故障发生。
---

4月份发生过一次运营平台故障，产生问题的原因比较典型，记录下来。

# 背景

使用Node构建运营平台，直接操作存储在ElasticSearch核心数据（和业务服务共享）。

# 故障描述

某日早上，推荐服务响应超时，几乎每隔一两分钟就发生，告警频繁。导致结果是app打开首页的个人模式没有收到歌曲推荐。
<!-- more -->
# 故障排查

1. 最近推荐服务没有升级，基本排除服务升级导致的异常。
2. 在对应的推荐接口中，会查询ElasticSearch获取数据。从打点日志看，有时候超时rt > 3000ms，但是通常很快返回。怀疑是ElasticSearch的问题。
3. 去ElasticSearch控制台看，发现慢查询，具体语句就不贴了，**是根据某个字段的更新时间扫描并排序，然后一次返回前面9999条记录**。基本每分钟都有一条这样的慢查询记录。初步怀疑是某个服务的定时任务触发的。
4. 印象中没有见过哪个后端服务写过有这查询语句。在后端服务用9999去全文搜索，没有找到对应的语句。
5. 于是问了运营后台同学，得知新增加了一个运营需求，展现最新修改xxx字段的记录。实现上是增加了一个每分钟执行的定时任务读取并且缓存数据。

至此，故障原因水落石出。

# 故障解决

1. 紧急停掉该运营后台的定时任务。推荐服务的告警就消失了。
2. 增加给查询字段索引。
3. 跟运营沟通，降低数据刷新间隔。先改为3小时刷新一次。后续再做优化。

# 反思

这个故障案例，虽然从发现、排查、临时修复，只用了20多分钟，但确是反映了日常研发活动中比较常见的几个问题。

## 测试用例覆盖

只测试了定时任务的功能，看结果是通过的。但是缺少了回归测试，没有对其他服务做回归和常态化压测。本质原因是自动化测试程度不高、服务测试和回归测试意识薄弱。在微服务中、尤其是共享存储的服务，很有必要提高测试质量和效率。

## 优化不足

这个典型会扫描全表的查询，并且没有走索引，再加上当时ES分片数量少，一旦数据量稍多，就会严重消耗ElasticSearch服务器资源，导致其他查询执行缓慢。对于运营定时任务来说，几秒的慢查询没什么。但是共享存储、对高并发业务来说就是致命的影响了。

## code review

如果有高质量的code review，完全可以扫描出来这个慢查询。

## 沟通

对于共享存储的服务，知会其他团队相应的修改还是有必要的，相当于有更多的人来review修改。可能多留个心眼，就有可能在上线之前觉察到问题。

## 存储隔离

事实上，共享存储通常不是一个很好的做法。但是目前来说，运营平台和业务服务直接共享同一份存储是合理的：
1. 目前数据量不大
2. 多份存储，涉及数据同步、更新等问题。目前系统处于快速迭代、不稳定阶段，把有限精力优先处理业务问题。

## 监控和告警

ElasticSearch控制台有慢记录功能，但是没有对接告警通道。如果接上了，排查这个问题就更快了。

## 需求的合理性

这个字段的数据需要每分钟刷新吗？
在出故障前，肯定说相当重要、无论如何也要做到、做不到就不如不做了、blablabla。
发生故障之后，就变成其实也没有那么重要啦、还是可以慢一点更新也每问题的。

有的运营需求，当时人总是觉得很合理很有必要，但是实际上用处不大，有时为了实现不合理的需求，引入不好的方案，最后挖坑背锅。开发人员也需要有产品意识，思考一个需求能为用户带来的价值，否则就会沦为搬砖工和背锅侠了。

