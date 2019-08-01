---
title: java状态机框架选型简单比较：stateless4j, spring statemachine, squirrel
date: 2019-07-02 10:13:43
tags: [设计模式, 系统设计]
categories: 设计模式
keywords: [stateless4j, spring statemachine, squirrel, java状态机框架]
description: 根据SD项目的技术选型需要，对3个常见的java状态机选型简单比较（spring statemachine、stateless4j、squirrel）。statelss4j功能最简单，适合二次改造，但已经停止维护。spring statemachine比较重型，能够和spring全家桶方便集成。squirrel在功能和设计复杂中比较平衡，推荐使用。
---

上一篇文章简单聊了状态模式。在实际应用，可以使用框架来实现状态机。

往期文章：
- {% post_link design-pattern-state %}

# 技术选型考虑

针对sd项目的选型要求：
- 简单，容易上手。
- 足够的扩展点，能够进行定制。
- 有真实项目应用。被线上项目验证，前人踩过坑，可靠性比较高。
- 可移植性（加分项）。目前状态机只是应用在服务器端，但实际上客户端的业务逻辑也可以使用状态模式。状态机框架能够移植到客户端，减轻客户端的编码负担。

# spring statemachine

基于java的框架，一般优先考虑spirng全家桶有无支持，恰好有[spring statemachine](https://projects.spring.io/spring-statemachine/)。

## 定义状态和事件

```java
static enum States {
    STATE1, STATE2
}

static enum Events {
    EVENT1, EVENT2
}
```

## 定义StateMachine

使用`StateMachineBuilder`构建`StateMachine`，定义事件转换（transition）和listener（可以使用注解方式）。
```java
public StateMachine<States, Events> buildMachine() throws Exception {
    Builder<States, Events> builder = StateMachineBuilder.builder();

    builder.configureStates()
        .withStates()
            .initial(States.STATE1)
            .states(EnumSet.allOf(States.class));

    builder.configureTransitions()
        .withExternal()
            .source(States.STATE1).target(States.STATE2)
            .event(Events.EVENT1)
            .and()
        .withExternal()
            .source(States.STATE2).target(States.STATE1)
            .event(Events.EVENT2);

    return builder.build();
}
```

## 定义transition

当状态发生改变，触发相应转换行为。`StateMachineListener`提供多个事件监听器：
```java
/**
 * {@code StateMachineListener} for various state machine events.
 *
 * @author Janne Valkealahti
 *
 * @param <S> the type of state
 * @param <E> the type of event
 */
public interface StateMachineListener<S,E> {

	void stateChanged(State<S,E> from, State<S,E> to);

	void stateEntered(State<S,E> state);

	void stateExited(State<S,E> state);

	void eventNotAccepted(Message<E> event);

	void transition(Transition<S, E> transition);

	void transitionStarted(Transition<S, E> transition);

	void transitionEnded(Transition<S, E> transition);

	void stateMachineStarted(StateMachine<S, E> stateMachine);

	void stateMachineStopped(StateMachine<S, E> stateMachine);

	void stateMachineError(StateMachine<S, E> stateMachine, Exception exception);

	void extendedStateChanged(Object key, Object value);

	void stateContext(StateContext<S, E> stateContext);

}
```

也可以使用注解方式进行配置
```java
@WithStateMachine
static class MyBean {

    @OnTransition(target = "STATE1")
    void toState1() {
    }

    @OnTransition(target = "STATE2")
    void toState2() {
    }
}
```

## 使用状态机

```java
StateMachine<States, Events> stateMachine = buildMachine();
stateMachine.start();
stateMachine.sendEvent(Events.EVENT1);
stateMachine.sendEvent(Events.EVENT2);
```

## 优缺点

优点：
- 上手比较简单
- 丰富的扩展点，例如transition、interceptor。

缺点：
- 作为spring全家桶系列，spring statemachine并不是很活跃。调研的时候一直停留在2.x版本（半年前，现在已经有3.x snapshot）。
- 某团队反映spring statemachine 1.x版本有bug，导致业务出故障，至于2.x版本情况如何，没有找到详细信息。
- 因为支持扩展点多，设计比较重型。


# stateless4j

[stateless4j](https://github.com/oxo42/stateless4j)是另一款使用比较多的状态机框架。官网上的例子很简单：

```java
StateMachineConfig<State, Trigger> phoneCallConfig = new StateMachineConfig<>();

phoneCallConfig.configure(State.OffHook)
        .permit(Trigger.CallDialed, State.Ringing);

phoneCallConfig.configure(State.Ringing)
        .permit(Trigger.HungUp, State.OffHook)
        .permit(Trigger.CallConnected, State.Connected);

// this example uses Java 8 method references
// a Java 7 example is provided in /examples
phoneCallConfig.configure(State.Connected)
        .onEntry(this::startCallTimer)
        .onExit(this::stopCallTimer)
        .permit(Trigger.LeftMessage, State.OffHook)
        .permit(Trigger.HungUp, State.OffHook)
        .permit(Trigger.PlacedOnHold, State.OnHold);

// ...

StateMachine<State, Trigger> phoneCall =
        new StateMachine<>(State.OffHook, phoneCallConfig);

phoneCall.fire(Trigger.CallDialed);
assertEquals(State.Ringing, phoneCall.getState());
```

## 优缺点

优点：
- 上手很简单
- 轻量级设计，即使移植到客户端使用也没问题
- 代码量少，即使二次开发也容易
- 网上使用例子多，其他团队也有使用，反馈好

缺点：
- 不活跃。上一个maven repo release已经是2014年了
- 扩展点少，只有`onEntry`，`onExit`，`permitIf`，`guard`，`action`等，没有`transition`的概念


# squirrel

[squirrel](https://github.com/hekailiang/squirrel)是一款热门的状态机框架。

```java
public class QuickStartSample {

    // 1. Define State Machine Event
    enum FSMEvent {
        ToA, ToB, ToC, ToD
    }

    // 2. Define State Machine Class
    @StateMachineParameters(stateType=String.class, eventType=FSMEvent.class, contextType=Integer.class)
    static class StateMachineSample extends AbstractUntypedStateMachine {
        protected void fromAToB(String from, String to, FSMEvent event, Integer context) {
            System.out.println("Transition from '"+from+"' to '"+to+"' on event '"+event+
                "' with context '"+context+"'.");
        }

        protected void ontoB(String from, String to, FSMEvent event, Integer context) {
            System.out.println("Entry State \'"+to+"\'.");
        }
    }

    public static void main(String[] args) {
        // 3. Build State Transitions
        UntypedStateMachineBuilder builder = StateMachineBuilderFactory.create(StateMachineSample.class);
        builder.externalTransition().from("A").to("B").on(FSMEvent.ToB).callMethod("fromAToB");
        builder.onEntry("B").callMethod("ontoB");

        // 4. Use State Machine
        UntypedStateMachine fsm = builder.newStateMachine("A");
        fsm.fire(FSMEvent.ToB, 10);

        System.out.println("Current state is "+fsm.getCurrentState());
    }
}
```

## 优缺点

优点：
- 文档写得丰富
- 支持的扩展点也多
- 相比spring statemachine，设计比较轻量，二次开发难度比spriing statemachine容易
- github活跃

缺点：
- 要找缺点的话，内部使用的例子少

# 结论

最后决定使用stateless4j。主要考虑是轻量级，以及日后打包方案推广到客户端。squirrel也是不错的，如果纯粹考虑服务器端使用会选择的。

