---
title: RocketMQ延迟消息
date: 2019-07-07 15:58:27
tags: [RocketMQ]
categories: [RocketMQ]
keywords: [RocketMQ, 延迟消息, 消息延迟时间]
description: RocketMQ延迟消息的源码分析。发送消息时设置delayTimeLevel属性。真正保存的topic是SCHEDULE_TOPIC_XXXX，队列是delayTimeLevel。ScheduleMessageService包含一个Timer线程，执行DeliverDelayedMessageTimerTask，对于到期的延迟消息，发送到原来的目标topic。
---

基于RocketMQ v4.5.1源码。

# 延迟级别配置

位于`org.apache.rocketmq.store.config.MessageStoreConfig`
```java
    private String messageDelayLevel = "1s 5s 10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h";
```
定义了18中延迟级别。消息延迟时间支持1秒、5秒直到2小时。也可以自定义，但是不太建议。**不支持任意精度的延迟**。

<!-- more -->

# 消费者发送延迟消息

```java
msg.setDelayTimeLevel(1);
```
设置delayTimeLevel属性。编号从1开始（见下文的`delayLevel2QueueId()`函数）

# 延迟消息的存储

`org.apache.rocketmq.store.CommitLog`处理消息的存储。

1. 如果发现消息property包含PROPERTY_DELAY_TIME_LEVEL字段，则更新tagsCode。
```java
public DispatchRequest checkMessageAndReturnSize(java.nio.ByteBuffer byteBuffer, final boolean checkCRC,
        final boolean readBody) {
// more code            
// Timing message processing
{
    String t = propertiesMap.get(MessageConst.PROPERTY_DELAY_TIME_LEVEL);
    if (ScheduleMessageService.SCHEDULE_TOPIC.equals(topic) && t != null) {
        int delayLevel = Integer.parseInt(t);
        if (delayLevel > this.defaultMessageStore.getScheduleMessageService().getMaxDelayLevel()) {
            delayLevel = this.defaultMessageStore.getScheduleMessageService().getMaxDelayLevel();
        }
        if (delayLevel > 0) {
            tagsCode = this.defaultMessageStore.getScheduleMessageService().computeDeliverTimestamp(delayLevel,
                storeTimestamp);
        }
    }
}
// more code       
}
```

2. 对于延迟消息，保留原来消息的property，真正保存在topic是SCHEDULE_TOPIC_XXXX，queueId是设定的延迟级别映射。映射方法也在`ScheduleMessageService`
```java
public PutMessageResult putMessage(final MessageExtBrokerInner msg) {
    // more code       
    final int tranType = MessageSysFlag.getTransactionValue(msg.getSysFlag());
    if (tranType == MessageSysFlag.TRANSACTION_NOT_TYPE
        || tranType == MessageSysFlag.TRANSACTION_COMMIT_TYPE) {
        // Delay Delivery
        if (msg.getDelayTimeLevel() > 0) {
            if (msg.getDelayTimeLevel() > this.defaultMessageStore.getScheduleMessageService().getMaxDelayLevel()) {
                msg.setDelayTimeLevel(this.defaultMessageStore.getScheduleMessageService().getMaxDelayLevel());
            }
            topic = ScheduleMessageService.SCHEDULE_TOPIC;
            queueId = ScheduleMessageService.delayLevel2QueueId(msg.getDelayTimeLevel());
            // Backup real topic, queueId
            MessageAccessor.putProperty(msg, MessageConst.PROPERTY_REAL_TOPIC, msg.getTopic());
            MessageAccessor.putProperty(msg, MessageConst.PROPERTY_REAL_QUEUE_ID, String.valueOf(msg.getQueueId()));
            msg.setPropertiesString(MessageDecoder.messageProperties2String(msg.getProperties()));
            msg.setTopic(topic);
            msg.setQueueId(queueId);
        }
    }
    // more code           
}    

public static int queueId2DelayLevel(final int queueId) {
    return queueId + 1;
}
public static int delayLevel2QueueId(final int delayLevel) {
    return delayLevel - 1;
}
```

# 延迟消息任务

1. `ScheduleMessageService`初始化一个Timer线程。然后对于每个`delayLevelTable`的元素，新建一个`DeliverDelayedMessageTimerTask`任务处理。`delayLevelTable`的生成参见`ScheduleMessageService.parseDelayLevel()`。
```java
public void start() {
        if (started.compareAndSet(false, true)) {
            this.timer = new Timer("ScheduleMessageTimerThread", true);
            for (Map.Entry<Integer, Long> entry : this.delayLevelTable.entrySet()) {
                Integer level = entry.getKey();
                Long timeDelay = entry.getValue();
                Long offset = this.offsetTable.get(level);
                if (null == offset) {
                    offset = 0L;
                }

                if (timeDelay != null) {
                    this.timer.schedule(new DeliverDelayedMessageTimerTask(level, offset), FIRST_DELAY_TIME);
                }
            }

            this.timer.scheduleAtFixedRate(new TimerTask() {

                @Override
                public void run() {
                    try {
                        if (started.get()) ScheduleMessageService.this.persist();
                    } catch (Throwable e) {
                        log.error("scheduleAtFixedRate flush exception", e);
                    }
                }
            }, 10000, this.defaultMessageStore.getMessageStoreConfig().getFlushDelayOffsetInterval());
        }
}
```
2. `DeliverDelayedMessageTimerTask`初始化的时候向timer注册任务。
```java
    class DeliverDelayedMessageTimerTask extends TimerTask {
        private final int delayLevel;
        private final long offset;

        @Override
        public void run() {
            try {
                if (isStarted()) {
                    this.executeOnTimeup();
                }
            } catch (Exception e) {
                // XXX: warn and notify me
                log.error("ScheduleMessageService, executeOnTimeup exception", e);
                ScheduleMessageService.this.timer.schedule(new DeliverDelayedMessageTimerTask(
                    this.delayLevel, this.offset), DELAY_FOR_A_PERIOD);
            }
        }
    }
```

核心逻辑在`executeOnTimeup`，具体步骤是：
- 获取SCHEDULE_TOPIC指定的delayLevel队列
```java
ConsumeQueue cq =
                ScheduleMessageService.this.defaultMessageStore.findConsumeQueue(SCHEDULE_TOPIC,
                    delayLevel2QueueId(delayLevel));
```
- 从offest开始，找到cq中已经到期的消息
- 把到期消息写入原来的topic和queue
```java
MessageExt msgExt = ScheduleMessageService.this.defaultMessageStore.lookMessageByOffset(offsetPy, sizePy);
if (msgExt != null) {
    try {
        MessageExtBrokerInner msgInner = this.messageTimeup(msgExt);
        PutMessageResult putMessageResult =
            ScheduleMessageService.this.writeMessageStore.putMessage(msgInner);
    // more code
    }
}
```
其中`messageTimeup()`方法把SCHEDULE_TOPIC中的消息转换为原来要投递的消息。主要是恢复topic和queue字段。
- 更新offset，再次注册定时任务
```java
nextOffset = offset + (i / ConsumeQueue.CQ_STORE_UNIT_SIZE);
ScheduleMessageService.this.timer.schedule(new DeliverDelayedMessageTimerTask(
    this.delayLevel, nextOffset), DELAY_FOR_A_WHILE);
ScheduleMessageService.this.updateOffset(this.delayLevel, nextOffset);
```

# 总结

ScheduleMessageService设计采用Timer类，而不是ScheduledExecutorService，有点坑。Timer类是单线程设计，一旦堆积的延迟消息多，可能发送滞后。
**RocketMQ的延迟消息≠定时消息，不支持任意精度的延迟**（但是阿里云上的RocketMQ商业版支持）。
