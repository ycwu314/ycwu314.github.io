---
title: orchestration vs choreography
date: 2019-07-17 20:12:44
tags: [微服务, soa]
categories: [微服务]
keywords: [orchestration, choreography, 编排, 协同]
description: orchestration是编排，中心化地控制相关服务。choreography是协同，服务之间通过去中心化的方式交互（例如订阅某个消息topic）。
---

不管是微服务还是SOA，都会涉及到2个容易混淆的概念：orchestration（编排）和choreography（协同，这是我喜欢的翻译）。

# 概念

这2个概念容易混淆的原因，在于中文翻译太坑爹了，什么编排、编制，让人摸不着头脑。直接看英文解释就很好理解了。

>orchestration
>管弦乐编曲
>an arrangement of events that attempts to achieve a maximum effect;

>choreography
>舞蹈编排
>the representation of dancing by symbols as music is represented by notes

{% asset_img orche-chore.png %}
[图片来源](https://myalltech.wordpress.com/2017/05/12/orchestration-vs/)


管弦乐有一个总指挥，引导各个乐器手怎么演奏，这是orchestration（编排）。
芭蕾舞表演者根据音乐节奏就可以翩翩起舞，这是choreography（协同）。

stackoverflow上有个关于二者区别很好的回答 [Orchestration vs. Choreography](https://stackoverflow.com/questions/4127241/orchestration-vs-choreography)


>Service orchestration represents a single centralized executable business process (the orchestrator) that coordinates the interaction among different services. The orchestrator is responsible for invoking and combining the services.
>The relationship between all the participating services are described by a single endpoint (i.e., the composite service). The orchestration includes the management of transactions between individual services. 
>Orchestration employs a centralized approach for service composition.

orchestration是中心化的控制流程。关联服务的关系由中心化节点描述。

>Service choreography is a global description of the participating services, which is defined by exchange of messages, rules of interaction and agreements between two or more endpoints. Choreography employs a decentralized approach for service composition.

choreography是去中心化的方式，服务之间的交互通过消息交换实现。

二者的区别：
>The choreography describes the interactions between multiple services, where as orchestration represents control from one party's perspective.

{% asset_img orche-chore-2.png %}
[图片来源](https://specify.io/assets/orchestration-vs-choreography-097566bf059109c51c8a95faaf3ea77092a626c2a63bc5f06ae0a7ade4a31378.png)

# 例子

新注册一个用户，客户服务（customer service）要通知积分服务（loyalty points service）初始化记录、通知邮政服务（post service）发送新客礼包、发送欢迎邮件（email service）。Orchestration和choreography风格的实现分别如下：
{% asset_img customer-service.png %}
[图片来源](https://specify.io/assets/orchestration-vs-choreography-examples-88fe81d21b600c136f594d43421e4f9576552116c178e4fb7e7cf2b8fc5c065f.png)

Orchestration: 由customer service作为中心服务，分别调用其他3个服务。如果发生异常，customer service会感知并且做出回滚或者补偿操作。

Choreography：customer service向topic发送“customer create event”，其他3个服务订阅这个topic，收到消息后执行各自的操作。这些服务是否执行失败，customer service并不知道；失败后如何操作，也不知道。需要更多的监控和异常协调。

通过上面的例子，可以看到Orchestration中心化地控制业务，会产生服务中心大脑。Choreography去中心地协调业务，降低业务耦合，但是会导致业务流程分散，需要强大的监控和异常协调机制补偿，技术复杂度更高。

# 总结

No silver bullet。
我的经验是，关键的、核心的、复杂的、一致性要求高的业务流程，更适合Orchestration方式。非关键的、简单的、一致性要求不高的业务流程，用Choreography即可。
