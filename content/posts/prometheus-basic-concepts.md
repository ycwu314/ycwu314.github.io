---
title: prometheus 基本概念
date: 2020-01-25 12:44:31
tags: [prometheus, 监控]
categories: [prometheus]
keywords: [prometheus 基本概念]
description: 了解prometheus的数据模型。
---

# 前言

prometheus采集的数据都以“时序数据”形式存储。
采样数据（sample）包含：
- 一个float64精度的数值
- 一个毫秒精度的时间戳

接下来了解Prometheus的数据模型。
<!-- more -->
# metrics & label

metric是一个时间序列的唯一标识。一个metric可以有多个可选的label属性。
```
<metric name>{<label name>=<label value>, ...}
```
命名满足正则模式：`[a-zA-Z_:][a-zA-Z0-9_:]*`。

metric代表一个通用的统计概念，例如`http_requests_total`。
label是同一个metric下面不同维度（dimension）的实例。例入http请求统计里面的`get`。

一些命名规范：
```
# 使用有意义的前缀代表一系列相关概念的metric，例如 http_ 
http_requests_total (for a unit-less accumulating count)
# 单位使用复数，使用基础计量单位
http_request_duration_seconds (for all HTTP requests)

# 汇总统计使用 _total 后缀
process_cpu_seconds_total (exported by many client libraries)

# label定义
api_http_requests_total - differentiate request types: operation="create|update|delete"
```

下面是一些springboot acturator集成Prometheus暴露的metrics：
```ini
# HELP jvm_threads_states_threads The current number of threads having NEW state
# TYPE jvm_threads_states_threads gauge
jvm_threads_states_threads{application="springboot_prometheus",state="blocked",} 0.0
jvm_threads_states_threads{application="springboot_prometheus",state="waiting",} 12.0
jvm_threads_states_threads{application="springboot_prometheus",state="timed-waiting",} 7.0
jvm_threads_states_threads{application="springboot_prometheus",state="runnable",} 10.0
jvm_threads_states_threads{application="springboot_prometheus",state="new",} 0.0
jvm_threads_states_threads{application="springboot_prometheus",state="terminated",} 0.0

# HELP http_server_requests_seconds  
# TYPE http_server_requests_seconds summary
http_server_requests_seconds_count{application="springboot_prometheus",exception="None",method="GET",outcome="CLIENT_ERROR",status="404",uri="/**",} 3.0
http_server_requests_seconds_sum{application="springboot_prometheus",exception="None",method="GET",outcome="CLIENT_ERROR",status="404",uri="/**",} 
```

# 基本的metrics

## counter

一种累加的 metric，典型的应用如：请求的个数，结束的任务数，出现的错误数等等。
只能累加，不能减少。可以在重启后reset。
```ini
# HELP jvm_classes_unloaded_classes_total The total number of classes unloaded since the Java virtual machine has started execution
# TYPE jvm_classes_unloaded_classes_total counter
jvm_classes_unloaded_classes_total{application="springboot_prometheus",} 1.0
```

## gauge

一种常规的 metric，典型的应用如：温度，运行的jvm线程的个数。可以任意加减。

```ini
# HELP jvm_threads_states_threads The current number of threads having NEW state
# TYPE jvm_threads_states_threads gauge
jvm_threads_states_threads{application="springboot_prometheus",state="blocked",} 0.0
jvm_threads_states_threads{application="springboot_prometheus",state="waiting",} 12.0
jvm_threads_states_threads{application="springboot_prometheus",state="timed-waiting",} 7.0
jvm_threads_states_threads{application="springboot_prometheus",state="runnable",} 10.0
jvm_threads_states_threads{application="springboot_prometheus",state="new",} 0.0
jvm_threads_states_threads{application="springboot_prometheus",state="terminated",} 0.0
```

## histogram

>A histogram samples observations (usually things like request durations or response sizes) and counts them in configurable buckets. It also provides a sum of all observed values.

Histogram 会在一段时间范围内对数据进行采样（通常是请求持续时间或响应大小等），并将其计入可配置的存储桶（bucket）中。可以对观察结果采样，分组及统计。

Histogram在Prometheus系统中的查询语言中，有三种作用：
- 对每个采样点进行统计，打到各个分类值中(bucket)
- 对每个采样点值累计和(sum)
- 对采样点的次数累计和(count)

度量指标名称: `[basename]`的柱状图, 上面三类的作用度量指标名称：
- `[basename]_bucket{le="上边界"}`, 这个值为小于等于上边界的所有采样点数量
- `[basename]_sum`
- `[basename]_count`

下面是Prometheus自带的监控数据
```ini
# HELP prometheus_http_response_size_bytes Histogram of response size for HTTP requests.
# TYPE prometheus_http_response_size_bytes histogram
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="100"} 0
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="1000"} 2
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="10000"} 2
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="100000"} 2
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="1e+06"} 2
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="1e+07"} 2
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="1e+08"} 2
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="1e+09"} 2
prometheus_http_response_size_bytes_bucket{handler="/api/v1/query",le="+Inf"} 2
prometheus_http_response_size_bytes_sum{handler="/api/v1/query"} 207
prometheus_http_response_size_bytes_count{handler="/api/v1/query"} 2
```

一般的直方图，是在区间中划分多个桶，彼此独立。但是Prometheus的直方图是累加的（**cumulative**），即后面一个bucket包含前面所有bucket的样本。

这样做的好处是，在抓取指标时就可以根据需要丢弃某些 bucket，这样可以在降低 Prometheus 维护成本的同时，还可以粗略计算样本值的分位数。

可以使用`relabel`丢弃不需要的bucket。可以丢弃任意的 bucket，但不能丢弃 `le="+Inf"` 的 bucket，因为 `histogram_quantile` 函数需要使用这个标签。

**Histogram 的统计精度受限于bucket数量。bucket越多，精度越高，但是数据增长很快。**

## summary

Summary 是采样点分位图统计，用于得到**数据的分布情况**。

首先要了解几个统计学的概念。

分位数
> 表示了在这个样本集中从小至大排列之后小于某值的样本子集占总样本集的比例

百分位 (来自百度百科)
>用99个数值或99个点，将按大小顺序排列的观测值划分为100个等分，则这99个数值或99个点就称为百分位数，分别以Pl，P2，…，P99代表第1个，第2个，…，第99个百分位数。第j个百分位数j=1,2…100。式中Lj，fj和CFj分别是第j个百分位数所在组的下限值、频数和该组以前的累积频数，Σf是观测值的数目。
>
>百分位通常用第几百分位来表示，如第五百分位，它表示在所有测量数据中，测量值的累计频次达5%。以身高为例，身高分布的第五百分位表示有5%的人的身高小于此测量值，95%的身高大于此测量值。
>
>第25百分位数又称第一个四分位数（First Quartile），用Q1表示；第50百分位数又称第二个四分位数（Second Quartile），用Q2表示；第75百分位数又称第三个四分位数（Third Quartile）,用Q3表示。若求得第p百分位数为小数，可完整为整数。
>
>分位数是用于衡量数据的位置的量度，但它所衡量的，不一定是中心位置。百分位数提供了有关各数据项如何在最小值与最大值之间分布的信息。
>
>第p百分位数是这样一个值，它使得至少有p%的数据项小于或等于这个值，且至少有(100-p)%的数据项大于或等于这个值。
百分位和数据分位。


Summary 是**在客户端直接聚合生成的百分位数**。

带有度量指标的`[basename]`的summary 在抓取时间序列数据展示。
- 观察时间的φ-quantiles (0 ≤ φ ≤ 1), 显示为`[basename]`{分位数="[φ]"}
- `[basename]_sum`， 是指所有观察值的总和
- `[basename]_count`, 是指已观察到的事件计数值

Prometheus自带的summary监控：
```ini
# HELP go_gc_duration_seconds A summary of the GC invocation durations.
# TYPE go_gc_duration_seconds summary
go_gc_duration_seconds{quantile="0"} 0
go_gc_duration_seconds{quantile="0.25"} 0
go_gc_duration_seconds{quantile="0.5"} 0
go_gc_duration_seconds{quantile="0.75"} 0
go_gc_duration_seconds{quantile="1"} 0.001996
go_gc_duration_seconds_sum 0.0039907
go_gc_duration_seconds_count 48
```

设置quantile={0.5: 0.05, 0.9: 0.01, 0.99: 0.001}。每个quantile后面还有一个数，0.5-quantile后面是0.05，0.9-quantile后面是0.01，而0.99后面是0.001。这些是我们设置的能容忍的误差。

# histogram vs summary

从官网复制（https://prometheus.io/docs/practices/histograms/）

|                                                                   | Histogram                                                                                                                                   | Summary                                                                                                        |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Required configuration                                            | Pick buckets suitable for the expected range of observed values.                                                                            | Pick desired φ-quantiles and sliding window. Other φ-quantiles and sliding windows cannot be calculated later. |
| Client performance                                                | Observations are very cheap as they only need to increment counters.                                                                        | Observations are expensive due to the streaming quantile calculation.                                          |
| Server performance                                                | The server has to calculate quantiles. You can use recording rules should the ad-hoc calculation take too long (e.g. in a large dashboard). | Low server-side cost.                                                                                          |
| Number of time series (in addition to the _sum and _count series) | One time series per configured bucket.                                                                                                      | One time series per configured quantile.                                                                       |
| Quantile error (see below for details)                            | Error is limited in the dimension of observed values by the width of the relevant bucket.                                                   | Error is limited in the dimension of φ by a configurable value.                                               |
| Specification of φ-quantile and sliding time-window              | Ad-hoc with Prometheus expressions.                                                                                                         | Preconfigured by the client.                                                                                   |
| Aggregation                                                       | Ad-hoc with Prometheus expressions.                                                                                                         | In general not aggregatable.                                                                                   |

划重点：
- histogram是server端计算。summary是client端计算。
- histogram可以灵活设置φ （因为是动态计算丫）。summary一旦设置不可以修改。
- histogram可以聚合(histogram_quantile)。summary不可以聚合（聚合不同客户端上报的百分数没有意义）
- histogram的精度受限于bucket数量。bucket越多，消耗越大存储空间。


如何选择：
- If you need to aggregate, choose histograms.
- Otherwise, choose a histogram if you have an idea of the range and distribution of values that will be observed. Choose a summary if you need an accurate quantile, no matter what the range and distribution of the values is.


# instance 和 job

- instance: 一个单独 scrape 的目标， 一般对应于一个进程。
- jobs: 一组同种类型的 instances（主要用于保证可扩展性和可靠性）

当 scrape 目标时，Prometheus 会自动给这个 scrape 的时间序列附加一些标签以便更好的分别，例如： instance，job。
- job: The configured job name that the target belongs to.
- instance: The `<host>`:`<port>` part of the target's URL that was scraped.

对于每个scrape的instance，Prometheus会自动增加采样到以下的时间序列：
- `up{job="<job-name>", instance="<instance-id>"}`: 1 if the instance is healthy, i.e. reachable, or 0 if the scrape failed.
- `scrape_duration_seconds{job="<job-name>", instance="<instance-id>"}`: duration of the scrape.
- `scrape_samples_post_metric_relabeling{job="<job-name>", instance="<instance-id>"}`: the number of samples remaining after metric relabeling was applied.
- `scrape_samples_scraped{job="<job-name>", instance="<instance-id>"}`: the number of samples the target exposed.
- `scrape_series_added{job="<job-name>", instance="<instance-id>"}`: the approximate number of new series in this scrape. New in v2.10

# 小结

- Histogram也能计算百分位数但精度受分桶影响很大，分桶少的话会使百分位数计算很不准确，而分桶多的话会使数据量成倍增加。Summary则是依靠原始数据计算出的百分位数，是很准确的值。
- 但是平时一般不用Summary，因为它无法聚合。想象一下，prometheus抓取了一个集群下多台机器的百分位数，我们怎么根据这些数据得到整个集群的百分位数呢？

# 参考

- [METRIC TYPES](https://prometheus.io/docs/concepts/metric_types/)
- [一文搞懂 Prometheus 的直方图](https://juejin.im/post/5d492d1d5188251dff55b0b5)
- [分位数(quantile)](https://www.cnblogs.com/gispathfinder/p/5770091.html)
- [metrics类型](https://www.bookstack.cn/read/prometheus-manual/concepts-metric_types.md)
- [一篇文章带你理解和使用Prometheus的指标](https://frezc.github.io/2019/08/03/prometheus-metrics/)
- [Prometheus 入门与实践](https://www.ibm.com/developerworks/cn/cloud/library/cl-lo-prometheus-getting-started-and-practice/index.html)