---
title: apdex分数：评估应用性能
date: 2020-03-25 11:48:32
tags: [监控]
categories: [监控]
keywords: [apdex分数]
description: apdex分数笔记。
---


Prometheus中遇到了apdex分数的例子，记录学习笔记。
<!-- more -->
```
(
  sum(rate(http_request_duration_seconds_bucket{le="0.3"}[5m])) by (job)
+
  sum(rate(http_request_duration_seconds_bucket{le="1.2"}[5m])) by (job)
) / 2 / sum(rate(http_request_duration_seconds_count[5m])) by (job)
```

Apdex 分数是一个评估应用性能的方式。
Apdex 定义了应用响应时间的最优门槛为 T，另外根据应用响应时间结合 T 定义了三种不同的性能表现：
- Satisfied（满意）：应用响应时间低于或等于 T（T 由性能评估人员根据预期性能要求确定）。
- Tolerating（可容忍）：应用响应时间大于 T，但同时小于或等于 4T。
- Frustrated（烦躁期）：应用响应时间大于 4T。

计算公式
```
Apdex = (Satisfied Count + Tolerating Count / 2) / Total Samples
```

T 值的选择对于最终的 Apdex 值也会有直接影响，越大的 T 值理论上来说会有更大的 Apdex 得分。
Apdex = 1 可以只是一个不断优化的方向，却不一定是要成为优化的目标。

