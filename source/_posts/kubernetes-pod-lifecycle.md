---
title: kubernetes pod lifecycle
date: 2019-10-06 11:55:22
tags: [kubernetes]
categories: [kubernetes]
keywords: [kubernetes pod 生命周期, pod lifecycle]
description: kubernetes pod 提供readinessProbe、livenessProbe、readinessGates等方式对容器/pod进行检查。restartPolicy对异常的pod进行处理。
---
# Pod lifecycle & status

{% asset_img kubernetes-pod-life-cycle-status.jpg kubernetes-pod-life-cycle-status %}
<!-- more -->
(图片来源：`https://godleon.github.io/blog/Kubernetes/k8s-Pod-Overview/`)

Pod 的 status 定义在 PodStatus 对象中，其中有一个 phase 字段。
下面是 phase 可能的值（复制粘贴自: [Pod 的生命周期](https://kubernetes.io/zh/docs/concepts/workloads/pods/pod-lifecycle/)）：
- 挂起（Pending）：Pod 已被 Kubernetes 系统接受，但有一个或者多个容器镜像尚未创建。等待时间包括调度 Pod 的时间和通过网络下载镜像的时间，这可能需要花点时间。
- 运行中（Running）：该 Pod 已经绑定到了一个节点上，Pod 中所有的容器都已被创建。至少有一个容器正在运行，或者正处于启动或重启状态。
- 成功（Succeeded）：Pod 中的所有容器都被成功终止，并且不会再重启。
- 失败（Failed）：Pod 中的所有容器都已终止了，并且至少有一个容器是因为失败终止。也就是说，容器以非0状态退出或者被系统终止。
- 未知（Unknown）：因为某些原因无法取得 Pod 的状态，通常是因为与 Pod 所在主机通信失败。

查看pod的状态：
```
# kubectl describe pod mytomcat-78c89857d6-428gg
Name:         mytomcat-78c89857d6-428gg
Namespace:    default
Priority:     0
Node:         izwz9h8m2chowowqckbcy0z/172.18.151.35
Start Time:   Mon, 30 Sep 2019 13:32:05 +0800
Labels:       app=tomcat
              pod-template-hash=78c89857d6
Annotations:  <none>
Status:       Running
IP:           10.1.1.15
IPs:
  IP:           10.1.1.15
Controlled By:  ReplicaSet/mytomcat-78c89857d6

Conditions:
  Type              Status
  Initialized       True 
  Ready             True 
  ContainersReady   True 
  PodScheduled      True 
```

每个 Pod 都拥有一个 PodStatus，里面包含 PodConditions 数组。
Type类型如下：

| Type | 描述 |
| ---- | ---- |
| PodScheduled    | Pod 已被调度到一个节点                      |
| Ready           | Pod 能够提供请求，应该被添加到负载均衡池中以提供服务 |
| Initialized     | 所有 init containers 成功启动                  |
| Unschedulable   | 调度器不能正常调度容器，例如缺乏资源或其他限制 |
| ContainersReady | Pod 中所有容器全部就绪                      |

`status` 字段是一个字符串，可能的值有 True、False 和 Unknown。


# 容器探针 (container probe)

Probe 是在容器上 kubelet 的定期执行的诊断，kubelet 通过调用容器实现的 Handler 来诊断。目前有三种 Handlers ：
- ExecAction：在容器内部执行指定的命令，如果命令以状态代码 0 退出，则认为诊断成功。
- TCPSocketAction：对指定 IP 和端口的容器执行 TCP 检查，如果端口打开，则认为诊断成功。
- HTTPGetAction：对指定 IP + port + path路径上的容器的执行 HTTP Get 请求。如果响应的状态代码大于或等于 200 且小于 400，则认为诊断成功。

每次探测可能有如下之一的结果：
- Success：容器诊断通过
- Failure：容器诊断失败
- Unknown：诊断失败，因此不应采取任何措施

kubelet 可以选择性地对运行中的容器进行两种探测器执行和响应：
- livenessProbe：指示容器是否正在运行，如果活动探测失败，则 kubelet 会杀死容器，并且容器将受其 重启策略 的约束。如果不指定活动探测，默认状态是 Success。
- readinessProbe：指示容器是否已准备好为请求提供服务，如果准备情况探测失败，则控制器会从与 Pod 匹配的所有服务的端点中删除 Pod 的 IP 地址。初始化延迟之前的默认准备状态是 Failure，如果容器未提供准备情况探测，则默认状态为 Success。

如果集成了springboot actuator，可以这样设置probe：
```yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mytomcat
spec:
  selector:
    matchLabels:
      app: tomcat
  replicas: 1
  template:
    metadata:
      labels:
        app: tomcat
    spec:
      containers:
      - name: tomcat
        image: tomcat
        ports:
        - containerPort: 8080
        readinessProbe:                 # ---- 准备状态检查 ----
          httpGet:
            path: /actuator/health
            port: 8080
          timeoutSeconds: 2             # 探测超时时长，单位：秒
          initialDelaySeconds: 60       # 初始化时间，单位：秒
        livenessProbe:                  # ---- 健康状态检查 ----
          httpGet:
            port: 8080
            path: /actuator/info
          failureThreshold: 3           # 最大失败次数
          timeoutSeconds: 2             # 探测超时时长，单位：秒
          initialDelaySeconds: 60       # 初始化时间，单位：秒
          periodSeconds: 5              # 探测时间间隔，单位：秒
          successThreshold: 1           # 失败后探测成功的最小连续成功次数
```

使用ExecAction的例子：
```yml
spec:
  containers:
  - name: liveness
    image: innerpeacez/k8s.gcr.io-busybox
    args:
    - /bin/sh
    - -c
    - touch /tmp/healthy; sleep 20; rm -rf /tmp/healthy; sleep 60
    livenessProbe:
      exec:
        command:
        - cat
        - /tmp/healthy
      initialDelaySeconds: 10
      periodSeconds: 5
```

使用TCPSocketAction的例子：
```yml
spec:
  containers:
  - name: liveness-tcpsocket
    image: innerpeacez/k8s.gcr.io-goproxy:0.1
    ports:
    - containerPort: 8080
    livenessProbe:
      tcpSocket:
        port: 8080
      initialDelaySeconds: 15
      periodSeconds: 20
```

# Pod readiness gate

在 kubernetes 1.14 中 readiness gate 发布了 stable 版本。可以在 pod spec 中定义要额外诊断的 status.conditions(预设值为 False)，而 pod condition 的定义必须是以 key/value 的型式。
```yml
Kind: Pod
...
spec:
  readinessGates:
    - conditionType: "www.example.com/feature-1"
status:
  conditions:
    - type: Ready
      status: "True"
      lastProbeTime: null
      lastTransitionTime: 2018-01-01T00:00:00Z
    - type: "www.example.com/feature-1"
      status: "False"
      lastProbeTIme: null
      lastTransitionTime: 2018-01-01T00:00:00Z
  containerStatuses:
    - containerID: docker://abcd...
      ready: true
...
```

开启readinessGates之后，同时满足以下条件，pod 才会被诊断为 ready：
- pod 中所有的 container 状态皆为 Ready
- 所有在 pod spec 中定义的 ReadinessGates 的状态皆为 True

# 重启策略

PodSpec 中有一个 restartPolicy 字段，可能的值为 Always、OnFailure 和 Never。默认为 Always。 
需要注意：
- restart policy 套用的范围是 pod 中的所有 container，而不是某一个。
- 失败的容器由 kubelet 以五分钟为上限的指数退避延迟（10秒，20秒，40秒…）重新启动，并在成功执行十分钟后重置。
- 一旦绑定到一个节点，Pod 将永远不会重新绑定到另一个节点。

# 容器探针 & 重启策略的使用

- 容器启动后，需要经历预热、初始化操作，才能对外服务，则配置readinessProbe。
- 容器运行的业务有健康度检查，只有处于健康状态才能对外服务（比如自动更新状态则不接受外部流量），则配置readinessProbe。
- 如果容器崩溃会不会卡死，自己crash掉，则不需要livenessProbe，由k8s根据restartPolicy处理。
- pod包含多个容器，可以使用readinessGates自定义就绪状态检查。

# 参考

- [Pod 的生命周期](https://kubernetes.io/zh/docs/concepts/workloads/pods/pod-lifecycle/)
- [[Kubernetes] Pod 的設計 & 相關運作機制](https://godleon.github.io/blog/Kubernetes/k8s-Pod-Overview/)
- [kuberbetes Pod 健康检查](https://blog.csdn.net/zhwyj1019/article/details/90447886)


