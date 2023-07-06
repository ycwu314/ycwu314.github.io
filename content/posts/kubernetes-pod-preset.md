---
title: kubernetes pod preset
date: 2019-10-08 10:20:18
tags: [kubernetes]
categories: [kubernetes]
keywords: [kubernetes pod preset]
description: pod preset 可以把公共信息注入到pod，从而简化pod模板的编写。
---

# pod preset 是什么

在 pod 创建时，用户可以使用 podpreset 对象将 secrets、卷挂载和环境变量等信息注入其中。
使用 Pod Preset 使得 pod 模板的作者可以不必为每个 Pod 明确提供所有信息。这样一来，pod 模板的作者就不需要知道关于该服务的所有细节。
<!-- more -->
需要注意的是，Pod Preset是namespace级别的对象，其作用范围只能是同一个命名空间下容器。

# pod preset 流程

以下来自官网文档 [Pod Preset](https://kubernetes.io/zh/docs/concepts/workloads/pods/podpreset/)：
- 检索所有可用的 PodPresets。
- 检查 PodPreset 标签选择器上的标签，看看其是否能够匹配正在创建的 Pod 上的标签。
- 尝试将由 PodPreset 定义的各种资源合并到正在创建的 Pod 中。
- 出现错误时，在该 Pod 上引发记录合并错误的事件，PodPreset 不会注入任何资源到创建的 Pod 中。
- 注释刚生成的修改过的 Pod spec，以表明它已被 PodPreset 修改过。注释的格式为 `podpreset.admission.kubernetes.io/podpreset-<pod-preset name>: <resource version>`

# 开启 pod preset

截至k8s v1.16，pod preset默认是关闭的。
如果不确认集群是否已开启 PodPreset 支持，可以通过 `kubectl api-versions` 命令查看是否存在该类型，或者 `kubectl get podpreset` 命令查看，如果没开启会提示 `error: the server doesn't have a resource type "podpreset"` 错误。

开启PodPreset：
- 1.开启API：在apiserver配置文件中增加--runtime-config=settings.k8s.io/v1alpha1=true
- 2.开启准入控制器：在apiserver配置文件中增加--enable-admission-control=PodPreset


我使用的是microk8s环境，根据官网（[Configuring MicroK8s services](https://microk8s.io/docs/)）指引，修改
>${SNAP_DATA}/args/kube-apiserver
>where
>${SNAP_DATA} points to /var/snap/microk8s/current

题外话：注意是/var/snap/microk8s/current目录，一开始跑到/snap/microk8s/current报错了😂。
```
root@iZwz9h8m2chowowqckbcy0Z:/snap/microk8s/current# mkdir args
mkdir: cannot create directory ‘args’: Read-only file system

root@iZwz9h8m2chowowqckbcy0Z:/snap/microk8s/current# mount | grep snap
/var/lib/snapd/snaps/core_7396.snap on /snap/core/7396 type squashfs (ro,nodev,relatime,x-gdu.hide)
/var/lib/snapd/snaps/core_7713.snap on /snap/core/7713 type squashfs (ro,nodev,relatime,x-gdu.hide)
tmpfs on /run/snapd/ns type tmpfs (rw,nosuid,noexec,relatime,size=204124k,mode=755)
/var/lib/snapd/snaps/minikube_4.snap on /snap/minikube/4 type squashfs (ro,nodev,relatime,x-gdu.hide)
/var/lib/snapd/snaps/microk8s_920.snap on /snap/microk8s/920 type squashfs (ro,nodev,relatime,x-gdu.hide)

root@iZwz9h8m2chowowqckbcy0Z:/snap/microk8s/current# ll /var/lib/snapd/snaps/microk8s_920.snap 
-rw------- 2 root root 187269120 Oct  7 13:31 /var/lib/snapd/snaps/microk8s_920.snap
```

更新配置后，重启apiserver
```
sudo systemctl restart snap.microk8s.daemon-apiserver
```

# 实验

通过pod preset，为每个容器增加TZ环境变量。保存为tz-preset.yml。
```yml
apiVersion: settings.k8s.io/v1alpha1
kind: PodPreset
metadata:
  name: tz-preset
spec:
  selector:
    matchLabels:
  env:
    - name: TZ
      value: Asia/Shanghai
```
`spec.selector.matchLabels`是必须的。如果为空，则匹配所有pod。

一个测试用的pod，保存为tz-pod.yml。
```yml
apiVersion: v1
kind: Pod
metadata:
  name: tz-preset
spec:
  containers:
  - name: tz-preset
    image: nginx
```

先创建preset对象，再创建pod
```
# kubectl create -f tz-preset.yml
# kubectl create -f tz-pod.yml
```

查看pod，pod preset会修改annotation。
```yml
# kubectl describe pod tz-preset
Name:         tz-preset
Namespace:    default
Priority:     0
Node:         izwz9h8m2chowowqckbcy0z/172.18.151.35
Start Time:   Tue, 08 Oct 2019 12:14:21 +0800
Labels:       <none>
Annotations:  podpreset.admission.kubernetes.io/podpreset-tz-preset: 99719
```
进入容器检查
```
# kubectl exec -it  tz-preset env | grep TZ
TZ=Asia/Shanghai
```

