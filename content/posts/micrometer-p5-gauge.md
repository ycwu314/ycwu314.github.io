---
title: micrometer系列5： gauge
date: 2020-02-22 16:21:07
tags: [micrometer, 监控]
categories: [监控]
keywords: [micrometer gauge]
description: gauge默认实现使用WeakReference关联真实的对象，可能导致value()返回NAN。
---

# gauge 

gauge是测量值，数值可以上下变化。
<!-- more -->
（ps. 对比counter，通常用于自增场景）
```java
/**
 * A gauge tracks a value that may go up or down. The value that is published for gauges is
 * an instantaneous sample of the gauge at publishing time.
 *
 */
public interface Gauge extends Meter {

    class Builder<T> {
        private final String name;
        private final ToDoubleFunction<T> f;
        private Tags tags = Tags.empty();
        // 默认是弱引用方式，可能导致value()返回Double.NAN
        private boolean strongReference = false;

        @Nullable
        private Meter.Id syntheticAssociation = null;

        // 被关联的对象
        @Nullable
        private final T obj;

        @Nullable
        private String description;

        @Nullable
        private String baseUnit;

        public Gauge register(MeterRegistry registry) {
            return registry.gauge(new Meter.Id(name, tags, baseUnit, description, Type.GAUGE, syntheticAssociation), obj,
                    strongReference ? new StrongReferenceGaugeFunction<>(obj, f) : f);
        }        
    }
}


@FunctionalInterface
public interface ToDoubleFunction<T> {
    double applyAsDouble(T value);
}    
```
gauge会关联真实对象，并且把从真实对象获取计数值，抽象为`ToDoubleFunction`。
DefaultGauge是基本实现，用WeakReference关联真实的对象。

使用例子：
```java
// 参数： 
// - metric name
// - 要关联的真实对象
// - ToDoubleFunction 的实现
Queue<Message> receivedMessages = registry.gauge("unprocessed.messages", new ConcurrentLinkedQueue<>(), ConcurrentLinkedQueue::size);
```
注册gauge直接返回了底层关联的真实对象，这和其他的metrics类型不一样。


```java
// maintain a reference to myGauge
AtomicInteger myGauge = registry.gauge("numberGauge", new AtomicInteger(0));

// ... elsewhere you can update the value it holds using the object reference
myGauge.set(27);
myGauge.set(11);
```
**反复手动更新gauge的值是无意义的。只有在发布时刻（publish time）的实例值才有意义。**

# 场景问题： 返回NAN

gauge使用过程中，常见问题是gauge测量值返回NAN。
DefaultGauge使用WeakReference关联gauge和真实对象。如果对象被回收，那么就回返回`NAN`。之所以使用WeakReference，是为了避免影响gc。

```java
public class DefaultGauge<T> extends AbstractMeter implements Gauge {

    private final WeakReference<T> ref;
    private final ToDoubleFunction<T> value;

    public DefaultGauge(Meter.Id id, @Nullable T obj, ToDoubleFunction<T> value) {
        super(id);
        this.ref = new WeakReference<>(obj);
        this.value = value;
    }

    public double value() {
        T obj = ref.get();
        if (obj != null) {
            try {
                return value.applyAsDouble(ref.get());
            }
            catch (Throwable ex) {
                logger.log("Failed to apply the value function for the gauge '" + getId().getName() + "'.", ex);
            }
        }
        return Double.NaN;
    }    
}
```

micormeter也提供了强引用的方式关联gauge和真实对象的方式。
```java
class StrongReferenceGaugeFunction<T> implements ToDoubleFunction<T> {
    /**
     * Holding a reference to obj inside of this function effectively prevents it from being
     * garbage collected. Implementors of {@link Gauge} can then assume that they should hold
     * {@code obj} as a weak reference.
     * <p>
     * If obj is {@code null} initially then this gauge will not be reported.
     */
    @Nullable
    @SuppressWarnings("FieldCanBeLocal")
    private final T obj;

    private final ToDoubleFunction<T> f;

    StrongReferenceGaugeFunction(@Nullable T obj, ToDoubleFunction<T> f) {
        this.obj = obj;
        this.f = f;
    }

    @Override
    public double applyAsDouble(T value) {
        return f.applyAsDouble(value);
    }
}
```

# 参考

- [Why is my Gauge reporting NaN or disappearing?](https://micrometer.io/docs/concepts#_why_is_my_gauge_reporting_nan_or_disappearing)
