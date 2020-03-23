---
title: Prometheus PromQL 入门
date: 2020-03-19 19:53:21
tags: [prometheus]
categories: [prometheus]
keywords: [promql, rate vs irate]
description: PromQL学习笔记。rate/irate函数。
---

Prometheus官网中PromQL学习笔记。
<!-- more -->

# PromeQL支持的数据类型

- Instant vector - 瞬时向量，相同timestamp的时序集合 （a set of time series containing a single sample for each time series, all sharing the same timestamp）
- Range vector - 范围向量，一个时间范围内不同时序的集合 （a set of time series containing a range of data points over time for each time series）
- Scalar - 标量，即浮点数
- String - 字符串

# Instant vector 选择器

通过向`{}` 里附加一组标签来进一步过滤时间序列。例如`jvm_memory_used_bytes{id=~"PS.*"}`
```
= : 选择与提供的字符串完全相同的标签。
!= : 选择与提供的字符串不相同的标签。
=~ : 选择正则表达式与提供的字符串（或子字符串）相匹配的标签。
!~ : 选择正则表达式与提供的字符串（或子字符串）不匹配的标签。
```

# Range Vector 选择器

时间范围通过时间范围选择器 `[]` 进行定义。`jvm_memory_used_bytes{id=~"PS.*"} [5m]`
```
s - seconds
m - minutes
h - hours
d - days
w - weeks
y - years
```

还支持offset，表示最近过去时间：
```
jvm_memory_used_bytes{id=~"PS.*"} offset 10m
```

**范围向量的表达式不能直接绘图**。

# 函数和例子

为了得到一堆计数器，在Windows系统本地安装了wmi_exporter插件，指标通过`http://localhost:9182/metrics`暴露。
`prometheus.yml`增加配置:
```yml
scrape_configs:
  - job_name: 'local-windows'
    scrape_interval: 5s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['127.0.0.1:9182']  
```

以网络发送流量做例子（`wmi_net_bytes_sent_total{nic="Intel_R__Wireless_AC_9560_160MHz"}`）。


## increase()

increase(v range-vector) 函数获取区间向量中的第一个和最后一个样本并返回其增长量, 它会在单调性发生变化时(如由于采样目标重启引起的计数器复位)自动中断。

## rate()

rate(v range-vector) 函数可以直接计算区间向量 v **在时间窗口内平均增长速率**，它会在单调性发生变化时(如由于采样目标重启引起的计数器复位)自动中断。该函数的返回结果不带有度量指标，只有标签列表。
**当时间区间小于等于scrape频率，则rate函数无法返回**。

例如我的scrape频率是5s一次，则
```
rate( wmi_net_bytes_sent_total{nic="Intel_R__Wireless_AC_9560_160MHz"} [5s] )
```
不返回数据。

rate() 函数返回值类型只能用计数器，在长期趋势分析或者告警中推荐使用这个函数。

## irate()

irate(v range-vector) 函数用于计算区间向量的增长率，但是其反应出的是**瞬时增长率**。irate 函数是通过**区间向量中最后两个两本数据**来计算区间向量的增长速率，它会在单调性发生变化时(如由于采样目标重启引起的计数器复位)自动中断。

## rate vs irate

irate 只能用于绘制快速变化的计数器，在长期趋势分析或者告警中更推荐使用 rate 函数。
Percona讲述Prometheus这2个函数问题的文章值得看下：[Better Prometheus rate() Function with VictoriaMetrics](https://www.percona.com/blog/2020/02/28/better-prometheus-rate-function-with-victoriametrics/)。

## 源码实现

rate等函数的实现见[functions.go](https://github.com/prometheus/prometheus/blob/master/promql/functions.go)

关于rate实现的讨论，有个好TMD长的讨论，以后再分析：
- [rate()/increase() extrapolation considered harmful #3746](https://github.com/prometheus/prometheus/issues/3746)

```go
// extrapolatedRate is a utility function for rate/increase/delta.
// It calculates the rate (allowing for counter resets if isCounter is true),
// extrapolates if the first/last sample is close to the boundary, and returns
// the result as either per-second (if isRate is true) or overall.
func extrapolatedRate(vals []parser.Value, args parser.Expressions, enh *EvalNodeHelper, isCounter bool, isRate bool) Vector {
	ms := args[0].(*parser.MatrixSelector)
	vs := ms.VectorSelector.(*parser.VectorSelector)

	var (
		samples    = vals[0].(Matrix)[0]
		rangeStart = enh.ts - durationMilliseconds(ms.Range+vs.Offset)
		rangeEnd   = enh.ts - durationMilliseconds(vs.Offset)
	)

	// No sense in trying to compute a rate without at least two points. Drop
	// this Vector element.
	if len(samples.Points) < 2 {
		return enh.out
	}
	var (
		counterCorrection float64
		lastValue         float64
	)
	for _, sample := range samples.Points {
		if isCounter && sample.V < lastValue {
			counterCorrection += lastValue
		}
		lastValue = sample.V
	}
	resultValue := lastValue - samples.Points[0].V + counterCorrection

	// Duration between first/last samples and boundary of range.
	durationToStart := float64(samples.Points[0].T-rangeStart) / 1000
	durationToEnd := float64(rangeEnd-samples.Points[len(samples.Points)-1].T) / 1000

  // 区间长度
	sampledInterval := float64(samples.Points[len(samples.Points)-1].T-samples.Points[0].T) / 1000
	averageDurationBetweenSamples := sampledInterval / float64(len(samples.Points)-1)

	if isCounter && resultValue > 0 && samples.Points[0].V >= 0 {
		// Counters cannot be negative. If we have any slope at
		// all (i.e. resultValue went up), we can extrapolate
		// the zero point of the counter. If the duration to the
		// zero point is shorter than the durationToStart, we
		// take the zero point as the start of the series,
		// thereby avoiding extrapolation to negative counter
		// values.
		durationToZero := sampledInterval * (samples.Points[0].V / resultValue)
		if durationToZero < durationToStart {
			durationToStart = durationToZero
		}
	}

	// If the first/last samples are close to the boundaries of the range,
	// extrapolate the result. This is as we expect that another sample
	// will exist given the spacing between samples we've seen thus far,
	// with an allowance for noise.
	extrapolationThreshold := averageDurationBetweenSamples * 1.1
	extrapolateToInterval := sampledInterval

	if durationToStart < extrapolationThreshold {
		extrapolateToInterval += durationToStart
	} else {
		extrapolateToInterval += averageDurationBetweenSamples / 2
	}
	if durationToEnd < extrapolationThreshold {
		extrapolateToInterval += durationToEnd
	} else {
		extrapolateToInterval += averageDurationBetweenSamples / 2
	}
  resultValue = resultValue * (extrapolateToInterval / sampledInterval)
  // increase 函数不用除以区间时间长度
	if isRate {
		resultValue = resultValue / ms.Range.Seconds()
	}

	return append(enh.out, Sample{
		Point: Point{V: resultValue},
	})
}

// === rate(node parser.ValueTypeMatrix) Vector ===
func funcRate(vals []parser.Value, args parser.Expressions, enh *EvalNodeHelper) Vector {
	return extrapolatedRate(vals, args, enh, true, true)
}

// === increase(node parser.ValueTypeMatrix) Vector ===
func funcIncrease(vals []parser.Value, args parser.Expressions, enh *EvalNodeHelper) Vector {
	return extrapolatedRate(vals, args, enh, true, false)
}

// === irate(node parser.ValueTypeMatrix) Vector ===
func funcIrate(vals []parser.Value, args parser.Expressions, enh *EvalNodeHelper) Vector {
	return instantValue(vals, enh.out, true)
}

func instantValue(vals []parser.Value, out Vector, isRate bool) Vector {
	samples := vals[0].(Matrix)[0]
	// No sense in trying to compute a rate without at least two points. Drop
	// this Vector element.
	if len(samples.Points) < 2 {
		return out
	}

  // 使用最近2个采样计算 
	lastSample := samples.Points[len(samples.Points)-1]
	previousSample := samples.Points[len(samples.Points)-2]

	var resultValue float64
	if isRate && lastSample.V < previousSample.V {
		// Counter reset.
		resultValue = lastSample.V
	} else {
		resultValue = lastSample.V - previousSample.V
	}

  // 使用最近2个采样计算 
	sampledInterval := lastSample.T - previousSample.T
	if sampledInterval == 0 {
		// Avoid dividing by 0.
		return out
	}

	if isRate {
		// Convert to per-second.
		resultValue /= float64(sampledInterval) / 1000
	}

	return append(out, Sample{
		Point: Point{V: resultValue},
	})
}
```

# 参考

- [QUERYING PROMETHEUS](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [PromQL内置函数](https://yunlzheng.gitbook.io/prometheus-book/parti-prometheus-ji-chu/promql/prometheus-promql-functions)
