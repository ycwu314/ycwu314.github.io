---
title: kubernates externalTrafficPolicy 笔记
date: 2020-01-17 10:12:41
tags: [kubernates]
categories: [kubernates]
keywords: [kubernates externalTrafficPolicy]
description:
---

在折腾nacos k8s部署的时候遇到 externalTrafficPolicy ，记录学习笔记。
<!-- more -->

# Headless Service

Headless Service的对应的每一个Endpoints，即每一个Pod，都会有对应的DNS域名；这样Pod之间就可以互相访问。
对于一些集群类型的应用就可以解决互相之间身份识别的问题了。
（与本文无关）

# externalTrafficPolicy

`service.spec.externalTrafficPolicy`: 表示此服务是否希望将外部流量路由到节点本地或集群范围的端点。
有两个可用选项：Cluster（默认）和 Local。Cluster 隐藏了客户端源 IP，可能导致第二跳到另一个节点，但具有良好的整体负载分布。Local 保留客户端源 IP 并避免 LoadBalancer 和 NodePort 类型服务的第二跳，但存在潜在的不均衡流量传播风险。

使用保留源 IP 的警告和限制:
>新功能中，外部的流量不会按照 pod 平均分配，而是在节点（node）层面平均分配（因为 GCE/AWS 和其他外部负载均衡实现没有能力做节点权重， 而是平均地分配给所有目标节点，忽略每个节点上所拥有的 pod 数量）。
>
>然而，在 pod 数量（NumServicePods） « 节点数（NumNodes）或者 pod 数量（NumServicePods） » 节点数（NumNodes）的情况下，即使没有权重策略，我们也可以看到非常接近公平分发的场景。


# podAntiAffinity

外部的流量不会按照 pod 平均分配，而是在节点（node）层面平均分配,那么我们能做的只有保证同一业务的pod调度到不同的node节点上。
podAntiAffinity使用场景：
- 将一个服务的POD分散在不同的主机或者拓扑域中，提高服务本身的稳定性。
- 给POD对于一个节点的独占访问权限来保证资源隔离，保证不会有其它pod来分享节点资源。
- 把可能会相互影响的服务的POD分散在不同的主机上

对于亲和性和反亲和性，每种都有三种规则可以设置：
- RequiredDuringSchedulingRequiredDuringExecution ：在调度期间要求满足亲和性或者反亲和性规则，如果不能满足规则，则POD不能被调度到对应的主机上。在之后的运行过程中，如果因为某些原因（比如修改label）导致规则不能满足，系统会尝试把POD从主机上删除（现在版本还不支持）。
- RequiredDuringSchedulingIgnoredDuringExecution ：在调度期间要求满足亲和性或者反亲和性规则，如果不能满足规则，则POD不能被调度到对应的主机上。在之后的运行过程中，系统不会再检查这些规则是否满足。
- PreferredDuringSchedulingIgnoredDuringExecution ：在调度期间尽量满足亲和性或者反亲和性规则，如果不能满足规则，POD也有可能被调度到对应的主机上。在之后的运行过程中，系统不会再检查这些规则是否满足。


# 参考

- [从service的externalTrafficPolicy到podAntiAffinity](https://segmentfault.com/a/1190000016033076)
- [创建一个外部负载均衡器](https://kubernetes.io/zh/docs/tasks/access-application-cluster/create-external-load-balancer/)


