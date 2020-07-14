---
title: kubernetes pod hook
date: 2019-10-07 18:54:12
tags: [kubernetes]
categories: [kubernetes]
keywords: [kubernetes pod hook]
description: pod有2个钩子：PostStart和PreStop。钩子处理程序的日志不会在 Pod 事件中公开。要使用describe命令在Events中查看。
---

# pod hook

Kubernetes为容器提供了生命周期钩子。 对于Pod，有以下2个hook：
<!-- more -->
- PostStart：这个钩子在容器创建后立即执行。但是，并不能保证钩子将在容器ENTRYPOINT之前运行，因为没有参数传递给处理程序（异步执行）。主要用于资源部署、环境准备等。 如果钩子运行或挂起的时间太长，则容器无法达到 running 状态。
- PreStop：这个钩子在容器终止之前立即被调用。它是阻塞的，意味着它是同步的， 所以它必须在删除容器的调用发出之前完成。主要用于优雅关闭应用程序、通知其他系统等。

针对容器，有两种类型的钩子处理程序可供实现：
- Exec - 执行一个特定的命令，例如 pre-stop.sh，在容器的 cgroups 和名称空间中。 命令所消耗的资源根据容器进行计算。
- HTTP - 对容器上的特定端点执行 HTTP 请求。

# 实验

在postStart操作执行完成之前，kubelet会锁住容器，不让应用程序的进程启动，只有在 postStart操作完成之后容器的状态才会被设置成为RUNNING。
```yml
apiVersion: v1
kind: Pod
metadata:
  name: pod-hook-demo
spec:
  containers:
  - name: pod-hook-demo
    image: nginx
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "sleep 30"]
      preStop:
        exec:
          command: ["/bin/sh", "-c", "echo Hello from the preStop handler > /usr/share/message"]
```

马上查看pod状态，返回pending。
```yml
root@iZwz9h8m2chowowqckbcy0Z:~/k8s# kubectl describe pod pod-hook-demo

Name:         pod-hook-demo
Namespace:    default
Priority:     0
Node:         izwz9h8m2chowowqckbcy0z/172.18.151.35
Start Time:   Mon, 07 Oct 2019 19:23:28 +0800
Labels:       <none>
Annotations:  <none>
Status:       Pending
IP:           
IPs:          <none>
Containers:
  pod-hook-demo:
    Container ID:   
    Image:          nginx
    Image ID:       
    Port:           <none>
    Host Port:      <none>
    State:          Waiting
      Reason:       ContainerCreating
    Ready:          False
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-rpvtx (ro)
```

# 日志

钩子处理程序的日志不会在 Pod 事件中公开。 如果处理程序由于某种原因失败，它将播放一个事件。 
对于 PostStart，这是 FailedPostStartHook 事件，对于 PreStop，这是 FailedPreStopHook 事件。

修改yml
```yml
apiVersion: v1
kind: Pod
metadata:
  name: pod-hook-demo
spec:
  containers:
  - name: pod-hook-demo
    image: nginx
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "exit 1"]
      preStop:
        exec:
          command: ["/bin/sh", "-c", "echo Hello from the preStop handler > /usr/share/message"]
```

```
Events:
  Type     Reason               Age              From                              Message
  ----     ------               ----             ----                              -------
  Normal   Scheduled            <unknown>        default-scheduler                 Successfully assigned default/pod-hook-demo to izwz9h8m2chowowqckbcy0z
  Normal   Killing              3s               kubelet, izwz9h8m2chowowqckbcy0z  FailedPostStartHook
  Normal   Pulled               3s               kubelet, izwz9h8m2chowowqckbcy0z  Successfully pulled image "nginx"
  Normal   Created              3s               kubelet, izwz9h8m2chowowqckbcy0z  Created container pod-hook-demo
  Normal   Started              3s               kubelet, izwz9h8m2chowowqckbcy0z  Started container pod-hook-demo
  Warning  FailedPostStartHook  3s               kubelet, izwz9h8m2chowowqckbcy0z  Exec lifecycle hook ([/bin/sh -c exit 1]) for Container "pod-hook-demo" in Pod "pod-hook-demo_default(3e094b95-d182-4938-be5b-c021d9df1dd2)" failed - error: command '/bin/sh -c exit 1' exited with 1: , message: ""
  Normal   Pulling              1s (x2 over 6s)  kubelet, izwz9h8m2chowowqckbcy0z  Pulling image "nginx"
```

# 对比init container

{% asset_img pod-init-process.jpg pod-init-process %}

一些初始化操作可以在init container或者postStart hook执行。
init container在main container之前执行。
PostStart hook在main container之中执行。