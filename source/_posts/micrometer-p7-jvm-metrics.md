---
title: micrometer系列7：jvm metrics
date: 2020-02-27 14:41:19
tags: [micrometer, 监控]
categories:  [监控]
keywords: [MeterBinder, jvm metrics]
description: micrometer默认提供jvm metrics的实现。
---

# MeterBinder

MeterBinder把metrics注册到MeterRegistry。
<!-- more -->
```java
/**
 * Binders register one or more metrics to provide information about the state
 * of some aspect of the application or its container.
 * <p>
 * Binders are enabled by default if they source data for an alert
 * that is recommended for a production ready app.
 */
public interface MeterBinder {
    void bindTo(@NonNull MeterRegistry registry);
}
```

`io.micrometer.core.instrument.binder.jvm`提供了jvm相关的指标：
- ClassLoaderMetrics
- DiskSpaceMetrics
- ExecutorServiceMetrics
- JvmGcMetrics
- JvmMemoryMetrics
- JvmThreadMetrics

`JvmMetricsAutoConfiguration`是springboot自动装配类，注册了gc、memory、thread、classloader的metrics。

# MeterBinder实现

## ClassLoaderMetrics

对于jvm metrics，实现上依赖JMX bean。
```java
@NonNullApi
@NonNullFields
public class ClassLoaderMetrics implements MeterBinder {
    private final Iterable<Tag> tags;

    public ClassLoaderMetrics() {
        this(emptyList());
    }

    public ClassLoaderMetrics(Iterable<Tag> tags) {
        this.tags = tags;
    }

    @Override
    public void bindTo(MeterRegistry registry) {
        // 通过jmx bean，获取对应的数值
        ClassLoadingMXBean classLoadingBean = ManagementFactory.getClassLoadingMXBean();

        // parameter: (String name, @Nullable T obj, ToDoubleFunction<T> f)
        Gauge.builder("jvm.classes.loaded", classLoadingBean, ClassLoadingMXBean::getLoadedClassCount)
                .tags(tags)
                .description("The number of classes that are currently loaded in the Java virtual machine")
                .baseUnit("classes")
                .register(registry);

        // 单调递增函数计数器
        FunctionCounter.builder("jvm.classes.unloaded", classLoadingBean, ClassLoadingMXBean::getUnloadedClassCount)
                .tags(tags)
                .description("The total number of classes unloaded since the Java virtual machine has started execution")
                .baseUnit("classes")
                .register(registry);
    }
}
```

## ExecutorServiceMetrics

micrometer也提供了线程池的metrics，需要手动注册。

```java
public void bindTo(MeterRegistry registry) {
    if (executorService == null) {
        return;
    }

    String className = executorService.getClass().getName();
    if (executorService instanceof ThreadPoolExecutor) {
        monitor(registry, (ThreadPoolExecutor) executorService);
    } else if (className.equals("java.util.concurrent.Executors$DelegatedScheduledExecutorService")) {
        monitor(registry, unwrapThreadPoolExecutor(executorService, executorService.getClass()));
    } else if (className.equals("java.util.concurrent.Executors$FinalizableDelegatedExecutorService")) {
        monitor(registry, unwrapThreadPoolExecutor(executorService, executorService.getClass().getSuperclass()));
    } else if (executorService instanceof ForkJoinPool) {
        monitor(registry, (ForkJoinPool) executorService);
    }
}
```

对于代理的线程池，先进行unwrap操作，获取底层的线程池。
```java
/**
 * Every ScheduledThreadPoolExecutor created by {@link Executors} is wrapped. Also,
 * {@link Executors#newSingleThreadExecutor()} wrap a regular {@link ThreadPoolExecutor}.
 */
@Nullable
private ThreadPoolExecutor unwrapThreadPoolExecutor(ExecutorService executor, Class<?> wrapper) {
    try {
        Field e = wrapper.getDeclaredField("e");
        e.setAccessible(true);
        return (ThreadPoolExecutor) e.get(executor);
    } catch (NoSuchFieldException | IllegalAccessException e) {
        // Do nothing. We simply can't get to the underlying ThreadPoolExecutor.
    }
    return null;
}
```


核心实现是montior方法，针对ThreadPoolExecutor和ForkJoinPool提供不同实现。
```java
private void monitor(MeterRegistry registry, @Nullable ThreadPoolExecutor tp) {
    if (tp == null) {
        return;
    }

    FunctionCounter.builder("executor.completed", tp, ThreadPoolExecutor::getCompletedTaskCount)
            .tags(tags)
            .description("The approximate total number of tasks that have completed execution")
            .baseUnit(BaseUnits.TASKS)
            .register(registry);
    // more codes
}
```


# 参考

- [JVM and System Metrics](https://micrometer.io/docs/ref/jvm)