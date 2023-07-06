---
title: springboot acturator 2 升级体验
date: 2020-03-17 20:44:36
tags: [springboot, java]
categories: [springboot]
keywords: [springboot acturator]
description: springboot acturator 2 升级体验。
---

# 背景

springboot从1.5.x升级到2.2.4，发现acturator有变化。特此记录。
<!-- more -->

# health详细信息

升级了acturator 2.x之后，health接口的详细信息没了，只有基本信息：
```json
{
    "status": "UP"
}
```

2.x默认配置不现实详细信息
```ini
management.endpoint.health.show-details=never
```
修改为
```
# when_authorized 或者 always
management.endpoint.health.show-details=when_authorized 
endpoints.health.sensitive=false 
```

这时候可以正常显示详细信息。
```java
// just for demo
@Component
public class LuckyHealthIndicator implements HealthIndicator {

    Random random = new Random();

    @Override
    public Health health() {
        return Health.up().withDetail("lucky", random.nextBoolean()).build();
    }
}
```
```json
"lucky": {
    "status": "UP",
    "details": {
        "lucky": false
    }
}
```

# 默认端点

2.x默认只放开`/health`和`/info`端点。
如果要放开所有端点，可以修改
```ini
management.endpoints.web.exposure.include=*
```

# metrics端点

1.x的metrics端点会显示各个metrics的详细信息。
2.x的metrics端点只会返回所有metrics名字。如果要获取具体的metrics详情，使用`/metrics/<指标名>`。
```json
{
    "names": [
        "jvm.threads.states",
        "jvm.memory.used",
        "jvm.memory.committed",
        "tomcat.sessions.rejected",
        "process.cpu.usage",
        "jvm.memory.max",
        "jvm.gc.pause",
        "jvm.classes.loaded",
        "jvm.classes.unloaded",
        "tomcat.sessions.active.current",
        "tomcat.sessions.alive.max",
        "jvm.gc.live.data.size",
        "jvm.buffer.count",
        "jvm.buffer.total.capacity",
        "tomcat.sessions.active.max",
        "process.start.time",
        "http.server.requests",
        "jvm.gc.memory.promoted",
        "logback.events",
        "jvm.gc.max.data.size",
        "system.cpu.count",
        "jvm.buffer.memory.used",
        "tomcat.sessions.created",
        "jvm.threads.daemon",
        "system.cpu.usage",
        "jvm.gc.memory.allocated",
        "tomcat.sessions.expired",
        "jvm.threads.live",
        "jvm.threads.peak",
        "process.uptime"
    ]
}
```

获取具体指标值： `http://localhost:8080/actuator/metrics/jvm.threads.states`
```json
{
    "name": "jvm.threads.states",
    "description": "The current number of threads having WAITING state",
    "baseUnit": "threads",
    "measurements": [
        {
            "statistic": "VALUE",
            "value": 33
        }
    ],
    "availableTags": [
        {
            "tag": "application",
            "values": [
                "springboot_prometheus"
            ]
        },
        {
            "tag": "state",
            "values": [
                "timed-waiting",
                "new",
                "runnable",
                "waiting",
                "blocked",
                "terminated"
            ]
        }
    ]
}
```

# 集成micrometer框架

2.x集成micrometer框架。自定义metrics直接使用micrometer的工具类。springboot也提供了MeterRegistry注入。

```java
@Component
public class FreeMemoryGauge {

    @Autowired
    private MeterRegistry meterRegistry;

    @PostConstruct
    public void init() {
        Gauge.builder("free.memory.gauge", Runtime.getRuntime()::freeMemory).description("free memory").baseUnit("bytes").register(meterRegistry);
    }

}
```

`http://localhost:8080/actuator/metrics/free.memory.gauge`
```json
{
    "name": "free.memory.gauge",
    "description": "free memory",
    "baseUnit": "bytes",
    "measurements": [
        {
            "statistic": "VALUE",
            "value": 274451032
        }
    ],
    "availableTags": [
        {
            "tag": "application",
            "values": [
                "springboot_prometheus"
            ]
        }
    ]
```

# 读写模型

在1.x中，Actuator遵循 R/W 模型，这意味着我们可以从中读取或写入它。
2.x版本现在支持CRUD模型，并且映射到http方法：
- @ReadOperation -它将映射到HTTP GET
- @WriteOperation - 它将映射到HTTP POST
- @DeleteOperation - 它将映射到HTTP DELETE

