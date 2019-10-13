---
title: kubernates pod 优雅关闭
date: 2019-10-08 20:01:17
tags: [kubernates]
categories: [kubernates]
keywords: [kubernates pod termination, k8s pod 优雅关闭]
description: kubernates pod 接受关闭命令后，进入优雅关闭阶段，处理preStop hook，发送SIGTERM信号。如果
---

# 优雅关闭

当一个进程关闭，通常要停止接受新的请求、处理完成当前请求、释放资源。这是优雅关闭（gracefully shutdown）的工作。
在k8s中，pod是一个运行在集群中的应用进程。k8s提供lifecycle hook、 grace period等机制，实现pod的优雅终止。
<!-- more -->

# pod 关闭流程

官网文章 [Termination of Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod/#termination-of-pods) 描述了pod关闭流程，摘录如下：
1. User sends command to delete Pod, with default grace period (30s)
2. The Pod in the API server is updated with the time beyond which the Pod is considered “dead” along with the grace period.
3. Pod shows up as “Terminating” when listed in client commands
4. (simultaneous with 3) When the Kubelet sees that a Pod has been marked as terminating because the time in 2 has been set, it begins the Pod shutdown process.
 - If one of the Pod’s containers has defined a preStop hook, it is invoked inside of the container. If the preStop hook is still running after the grace period expires, step 2 is then invoked with a small (2 second) extended grace period.
 - The container is sent the TERM signal. Note that not all containers in the Pod will receive the TERM signal at the same time and may each require a preStop hook if the order in which they shut down matters.
5. (simultaneous with 3) Pod is removed from endpoints list for service, and are no longer considered part of the set of running Pods for replication controllers. Pods that shutdown slowly cannot continue to serve traffic as load balancers (like the service proxy) remove them from their rotations.
6. When the grace period expires, any processes still running in the Pod are killed with SIGKILL.
7. The Kubelet will finish deleting the Pod on the API server by setting grace period 0 (immediate deletion). The Pod disappears from the API and is no longer visible from the client.

简单来说，发送delete pod命令后，pod标记为terminating状态，从service endpoint列表摘除，并且进入grace period（优雅关闭）阶段。
如果配置了preStop hook，则执行之。
如果grace period到时间了，preStop hook还没有退出，则延长额外的2s，之后向容器的主进程（pid=1的进程）发送 SIGTERM  信号。
当grace peroid结束后，k8s向还没结束的pod发送SIGKILL信号。

关于pod lifecycle hook，在这篇文章有介绍：
- {% post_link kubernates-pod-lifecycle %}

关于sigterm、sigkill的区别，可以看这篇文章：
- {% post_link linux-signal %}

# 修改优雅关闭时间

默认的优雅关闭时间是30s。

1. 在yaml文件配置`terminationGracePeriodSeconds`字段
```
apiVersion: v1
kind: Deployment
metadata:
    name: test
spec:
    replicas: 1
    template:
        spec:
            containers:
              - name: test
                image: ...
            terminationGracePeriodSeconds: 60
```

2. 手动指定
```
kubectl delete pod <pod_name> --grace-period=<seconds>
```
如果要强制删除pod
```
kubectl delete pod <pod_name> --grace-period=0 --force
```



