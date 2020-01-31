---
title: micrometer 源码简析，part 1
date: 2020-01-27 17:17:09
tags: [prometheus, micrometer]
categories: [micrometer]
keywords: [prometheus micrometer]
description: 从集成 Prometheus 来入手分析 micrometer 框架。
---

# micrometer 简介

micrometer是一个监控门面（facade）框架，用于对接各种不同的监控系统，其作用类似日志门面框架slf4j。
java应用对接Prometheus监控，可以直接使用Prometheus client，也可以使用micrometer框架。
<!-- more -->

在springboot应用引入`micrometer-registry-prometheus`
```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
    <version>1.3.3</version>
</dependency>
```
隐式导入
```xml
  <dependencies>
    <dependency>
      <groupId>io.micrometer</groupId>
      <artifactId>micrometer-core</artifactId>
      <version>1.3.3</version>
      <scope>compile</scope>
    </dependency>
    <dependency>
      <groupId>io.prometheus</groupId>
      <artifactId>simpleclient_common</artifactId>
      <version>0.7.0</version>
      <scope>compile</scope>
    </dependency>
  </dependencies>
```

# Prometheus metrics 自动配置

`PrometheusMetricsExportAutoConfiguration`自动配置prometheus metrics。
```java
package org.springframework.boot.actuate.autoconfigure.metrics.export.prometheus;

@Configuration(proxyBeanMethods = false)
@AutoConfigureBefore({ CompositeMeterRegistryAutoConfiguration.class, SimpleMetricsExportAutoConfiguration.class })
@AutoConfigureAfter(MetricsAutoConfiguration.class)
@ConditionalOnBean(Clock.class)
@ConditionalOnClass(PrometheusMeterRegistry.class)
@ConditionalOnProperty(prefix = "management.metrics.export.prometheus", name = "enabled", havingValue = "true",
		matchIfMissing = true)
@EnableConfigurationProperties(PrometheusProperties.class)
public class PrometheusMetricsExportAutoConfiguration {
}
```
很简单，不展开了。


# micrometer metric types

micrometer 定义的metric类型在`io.micrometer.core.instrument.Meter`
```java
enum Type {
    COUNTER,
    GAUGE,
    LONG_TASK_TIMER,
    TIMER,
    DISTRIBUTION_SUMMARY,
    OTHER;
}
```

原生Prometheus client定义metric类型在`io.prometheus.client.Collector`
```java
public enum Type {
  COUNTER,
  GAUGE,
  SUMMARY,
  HISTOGRAM,
  UNTYPED,
}
```

二者的类型不是一一对应。micrometer的metric类型和Prometheus在`PrometheusMeterRegistry`中进行映射：
```java
    protected Meter newMeter(Meter.Id id, Meter.Type type, Iterable<Measurement> measurements) {
        Collector.Type promType = Collector.Type.UNTYPED;
        switch (type) {
            case COUNTER:
                promType = Collector.Type.COUNTER;
                break;
            case GAUGE:
                promType = Collector.Type.GAUGE;
                break;
            case DISTRIBUTION_SUMMARY:
            case TIMER:
                promType = Collector.Type.SUMMARY;
                break;
        }

        MicrometerCollector collector = collectorByName(id);
        List<String> tagValues = tagValues(id);

        // more codes
    }
```
注意，micrometer的timer对应Prometheus的histogram，但是映射为Prometheus的summary类型。

# 暴露Prometheus指标

`PrometheusMeterRegistry`的scrape()对外暴露Prometheus指标。
```java
public String scrape() {
    Writer writer = new StringWriter();
    try {
        scrape(writer);
    } catch (IOException e) {
        // This actually never happens since StringWriter::write() doesn't throw any IOException
        throw new RuntimeException(e);
    }
    return writer.toString();
}

public void scrape(Writer writer) throws IOException {
    TextFormat.write004(writer, registry.metricFamilySamples());
}
```

`io.prometheus.client.exporter.common.TextFormat`根据version 0.0.4暴露Prometheus指标。prometheus指标协议具体见[EXPOSITION FORMATS](https://prometheus.io/docs/instrumenting/exposition_formats/)。


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