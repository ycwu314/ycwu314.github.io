---
title: 设计模式系列：状态模式
date: 2019-06-20 14:31:02
tags: [设计模式]
categories: 设计模式
keywords: [设计模式, 状态模式]
---

# 引子

在OA系统发起请求，可能会经历草稿、等待1级审批、等待2级审批、审批不通过、转交关联方处理、关联方处理完毕、正常关闭、取消等状态。随着状态变化，系统的行为也不一样，可能是通知审核人，可能是通知外部系统处理，等等。

再来一个例子：tcp连接，经历3次握手、数据传输、4次挥手阶段。在不同阶段，os进行初始化socket资源、设置tcp头部字段、校验远程连接的响应内容、注册超时器、释放资源等操作。

![The TCP Finite State Machine (FSM)](http://tcpipguide.com/free/diagrams/tcpfsm.png)
(图片来源 http://tcpipguide.com/free/t_TCPOperationalOverviewandtheTCPFiniteStateMachineF-2.htm)

这个2个例子都有共同的特点：
- 内部状态的改变，影响了系统的行为
- 有大量的状态和状态判断

设计模式中有“状态模式”优化这种场景的代码设计。

# 状态模式

允许一个对象在其内部状改变时改变它的行为。
主要解决的是当控制一个对象状态迁移的条件表达式过于复杂时的情况。把状态的判断逻辑转移到表示不同的一系列类当中，可以把复杂的逻辑判断简单化。

# 适用场景

一个对象在其内部状改变时改变它的行为。有大量判断状态的代码。

# 角色

- 状态管理器（StateManager）：有状态的对象，持有具体状态类，定义感兴趣的行为
- 抽象状态类（State）：定义与StateManager行为相关的接口
- 具体状态类（ConcreteState）：实现具体与StateManager行为相关的接口

{% asset_img state_class_diagram.png %}

# demo

```java
public class TestStatePattern {

    public static void main(String[] args) {
        LightManager lightManager = new LightManager();
        IState onState = new LightOnState();
        lightManager.setState(onState);

        System.out.println("current state is " + lightManager.getState());
        lightManager.tap();
        lightManager.tap();
        lightManager.tap();
    }
}

class LightManager {

    private IState state;

    public IState getState() {
        return state;
    }

    public void setState(IState state) {
        this.state = state;
    }

    public void tap() {
        if (state == null) {
            throw new IllegalArgumentException("state is null");
        }

        state.doProcess(this);
    }
}

interface IState {
    void doProcess(LightManager context);

}

class LightOnState implements IState {

    @Override
    public void doProcess(LightManager context) {
        System.out.println("light is off...");
        context.setState(new LightOffState());
    }

    @Override
    public String toString() {
        return "on";
    }
}

class LightOffState implements IState {

    @Override
    public void doProcess(LightManager context) {
        System.out.println("light is on...");
        context.setState(new LightOnState());
    }

    @Override
    public String toString() {
        return "off";
    }
}
```

# 优点

- 要列出所有状态，强制加深对业务流程的理解。
- 状态判断逻辑分散到各个具体的状态类，消灭了庞大的if...else、switch...case判断状态。
- 状态迁移规则封装到各个具体的状态类，修改某个状态类的行为，不影响其他状态类，每个类的行为是高内聚的。

# 缺点

1. 每个状态对应一个类，状态的增加会导致类数量增加。
2. 增加新的状态类，涉及到从旧的状态迁移到新的状态，则要修改对应的旧状态类。因此不满足OCP原则。

对于1)，算不上什么问题啦。新增一个类，远比修改一个1000行的类要安全多了。另外，状态的数量也不是无限膨胀的。
对于2)，才是问题。新的状态引入，肯定会有状态迁移到新的状态，必须要对迁移路径做回归测试。


# 和其他模式的对比

State模式和Strategy模式在实现上比较相似，但意图却大相径庭。
State模式强调对象内部状态的变化改变对象的行为，而客户端不需要关心状态迁移。
Strategy模式重点是外部条件决定对策略的选择，客户端可以指定使用的策略。

# 实践

状态模式处理的核心问题是状态迁移路径。在实践中，先列出系统的各个状态，再画出转换路径。
**转换路径要考虑是否可重入（reentrant）**。对于状态可重入，要考虑正常业务下，是否会永远在此状态永远循环不能退出的场景。

我在实际工作中遇到的问题是，业务定下来，状态机也设计了，砖也般，这时产品想法又改变，引入几个新的状态，导致状态迁移很复杂。技术leader对状态模式和状态机理解又不够透彻，为什么加几个状态影响这么大（估计也没搬过类似的砖头）。

在实践中，推荐使用状态机框架来实现。尽管自己写状态机也不复杂，采用框架优势的是状态迁移路径变得清晰，代码可读性高。以下代码来自[stateless4j](https://github.com/oxo42/stateless4j)。
```java
StateMachineConfig<State, Trigger> phoneCallConfig = new StateMachineConfig<>();

phoneCallConfig.configure(State.OffHook)
        .permit(Trigger.CallDialed, State.Ringing);

phoneCallConfig.configure(State.Ringing)
        .permit(Trigger.HungUp, State.OffHook)
        .permit(Trigger.CallConnected, State.Connected);

phoneCallConfig.configure(State.Connected)
        .onEntry(this::startCallTimer)
        .onExit(this::stopCallTimer)
        .permit(Trigger.LeftMessage, State.OffHook)
        .permit(Trigger.HungUp, State.OffHook)
        .permit(Trigger.PlacedOnHold, State.OnHold);

StateMachine<State, Trigger> phoneCall =
        new StateMachine<>(State.OffHook, phoneCallConfig);

phoneCall.fire(Trigger.CallDialed);
assertEquals(State.Ringing, phoneCall.getState());
```
phoneCallConfig把状态迁移路径和行为都集中配置在一起，整体脉络比较清晰。

