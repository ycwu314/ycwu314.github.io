---
title: microk8s之k8s.gcr.io访问问题
date: 2019-09-28 17:12:04
tags: [kubernetes, microk8s]
categories: [kubernetes]
keywords: [microk8s k8s.gcr.io, k8s.gcr.io 不能访问]
description: 手动导入k8s.gcr.io镜像到microk8s.ctr。
---

为了学习k8s，在ecs上安装单机版。
网上查资料对比了minikube和microk8s，最终使用microk8s。
<!-- more -->

# 安装microk8s
```
snap install microk8s --classic
```
**安装的是v1.15**。

# 设置别名（可选）
microk8s的工具都带有`microk8s.`前缀，可以增加别名简化kubectl使用：
```
vi .bashrc

alias kubectl=/snap/bin/microk8s.kubectl
```

# kubectl run

为了最基本体验，先启动一个tomcat试试。
```
kubectl run mytomcat --image=tomcat
```
查看pod状态，发现一直是`ContainerCreating`状态
```
kubectl get pod
```
于是使用describe命令查看pod
```
kubectl describe pod xxx
```
最后面日志如下
```
Events:
  Type     Reason                  Age                   From                              Message
  ----     ------                  ----                  ----                              -------
  Warning  FailedCreatePodSandBox  22m (x33 over 69m)    kubelet, izwz9h8m2chowowqckbcy0z  Failed create pod sandbox: rpc error: code = Unknown desc = failed to get sandbox image "k8s.gcr.io/pause:3.1": failed to pull image "k8s.gcr.io/pause:3.1": failed to resolve image "k8s.gcr.io/pause:3.1": no available registry endpoint: failed to do request: Head https://k8s.gcr.io/v2/pause/manifests/3.1: dial tcp 108.177.97.82:443: i/o timeout
```
这是pod的sandbox镜像拉取失败。

网上查资料，k8s.gcr.io/pause:3.1是存放在google cloud上的镜像，由于众所周知的原因，访问失败了。
解决的方法有：
1. 科学爱国
2. 手动下载镜像

第1种方法就不多说了。
这里采用第2种方法。

安装docker
```
apt-get install docker.io
```
感谢微软azure提供gcr镜像下载：[地址](http://mirror.azure.cn/help/gcr-proxy-cache.html )
```
docker pull gcr.azk8s.cn/google_containers/pause:3.1
docker tag gcr.azk8s.cn/google_containers/pause:3.1 k8s.gcr.io/pause:3.1
```
下载镜像后，再手动修改tag。

但是再次kubectl run依然报错。
网上查资料，microk8s使用自己内置的容器服务`microk8s.docker`，而非系统的docker。
但是
```
# microk8s.docker
microk8s.docker: command not found
```
**v1.14之后microk8s使用containerd代替dockerd**，具体可见这个[issue](https://github.com/ubuntu/microk8s/issues/382)
>Indeed in the 1.14 release contanerd replaced dockerd.

要么使用私有仓库registry，要么手动把docker镜像导入到containerd。microk8s官网提供了例子：[Working with locally built images without a registry](https://microk8s.io/docs/working)。
这里先使用手动操作，以后再建立私有仓库
```
docker save k8s.gcr.io/pause:3.1 > pause.tar
microk8s.ctr -n k8s.io image import pause.tar
```
`-n`是指定namespace。`microk8s.ctr -n k8s.io image ls`，看到导入的镜像了：
```
k8s.gcr.io/pause:3.1                                                                             application/vnd.oci.image.manifest.v1+json                sha256:3efe4ff64c93123e1217b0ad6d23b4c87a1fc2109afeff55d2f27d70c55d8f73 728.9 KiB linux/amd64 io.cri-containerd.image=managed 
```

终于启动成功了
```
Events:
  Type     Reason             Age                   From                              Message
  ----     ------             ----                  ----                              -------
  Normal   Scheduled          <unknown>             default-scheduler                 Successfully assigned default/mytomcat-75b679fc45-gftfw to izwz9h8m2chowowqckbcy0z
  Normal   Pulling            33m                   kubelet, izwz9h8m2chowowqckbcy0z  Pulling image "tomcat"
  Normal   Pulled             33m                   kubelet, izwz9h8m2chowowqckbcy0z  Successfully pulled image "tomcat"
  Normal   Created            33m                   kubelet, izwz9h8m2chowowqckbcy0z  Created container mytomcat
  Normal   Started            33m                   kubelet, izwz9h8m2chowowqckbcy0z  Started container mytomcat
```

[这里](https://www.jianshu.com/p/02fd2540fab2)有另一种解决k8s.gcr.io访问问题的思路，就是更换仓库名：
- 修改/var/snap/microk8s/current/args/kubelet。 添加--pod-infra-container-image=s7799653/pause:3.1
- 修改/var/snap/microk8s/current/args/containerd-template.toml的plugins -> plugins.cri -> sandbox_image为s7799653/pause:3.1


# 小结

手动下载、tag、导入k8s.gcr.io镜像到microk8s的contianerd：
```
docker pull gcr.azk8s.cn/google_containers/<imagename>:<version>
docker tag gcr.azk8s.cn/google_containers/<imagename>:<version> k8s.gcr.io/<imagename>:<version>
docker save k8s.gcr.io/<imagename>:<version> > <imagename>.tar
microk8s.ctr -n k8s.io image import <imagename>.tar
```