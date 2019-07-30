---
title: stateless4j踩坑经历
date: 2019-07-02 15:31:59
tags: [设计模式, 状态模式, 故障案例]
categories: 故障案例
keywords: [stateless4j, java状态机]
description: stateless4j是一个轻量级的java状态机框架，但是太久没有更新，master分支代码和maven repository上的版本有差异。建议使用master分支代码打包一份jar，上传到私服。
---

上次聊了java状态机框架选型，最后采用stateless4j。这次继续聊下stateless4j使用的坑。

往期文章：
- {% post_link compare-state-machine-framework %}

# 问题

调研的时候使用的代码是从 https://github.com/oxo42/stateless4j 下载。然后写了test case，简单验证业务逻辑，没毛病。
这时候在正式项目中引用stateless4j
```xml
    <dependency>
        <groupId>com.github.oxo42</groupId>
        <artifactId>stateless4j</artifactId>
        <version>2.5.0</version>
    </dependency>
```
结果idea报错方法找不到：`permitIf(T trigger, S destinationState, FuncBoolean guard, Action action)`

master代码
```java
    /**
     * Accept the specified trigger and transition to the destination state if guard is true
     * <p>
     * Additionally a given action is performed when transitioning. This action will be called after
     * the onExit action of the current state and before the onEntry action of
     * the destination state.
     *
     * @param trigger          The accepted trigger
     * @param destinationState The state that the trigger will cause a transition to
     * @param guard            Function that must return true in order for the trigger to be accepted
     * @param action           The action to be performed "during" transition
     * @return The receiver
     */
    public StateConfiguration<S, T> permitIf(T trigger, S destinationState, FuncBoolean guard, Action action) {
        enforceNotIdentityTransition(destinationState);
        return publicPermitIf(trigger, destinationState, guard, action);
    }
```

对比maven repo v2.5.0的代码，只有这个方法
```java
    /**
     * Accept the specified trigger and transition to the destination state
     *
     * @param trigger          The accepted trigger
     * @param destinationState The state that the trigger will cause a transition to
     * @param guard            Function that must return true in order for the trigger to be accepted
     * @return The reciever
     */
    public StateConfiguration<S, T> permitIf(T trigger, S destinationState, FuncBoolean guard) {
        enforceNotIdentityTransition(destinationState);
        return publicPermitIf(trigger, destinationState, guard);
    }
```

# 解决

在stateless4j repo拉下master分支，重新打包2.5.1，放到内部仓库。
