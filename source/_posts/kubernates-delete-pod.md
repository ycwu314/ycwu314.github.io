---
title: kubernates删除pod，自动重启
date: 2019-09-29 14:01:03
tags: [kubernates]
categories: [kubernates]
keywords: [kubernates delete pod]
description: 直接删除pod，由于relipcation的原因，kubernates自动用旧的pod spec创建pod。解决方式：1. 删除deployment对象 2. 直接更新spec，让k8s自动更新pod。
---

# 问题

使用kubectl run命令创建pod，发现漏了参数，想直接删除pod，再创建。但是kubernates会自动用之前的pod定义再次生成pod。
<!-- more -->
删除pod
```
kubectl delete pod <pod_name>
```

# 解决

直接删除deployment
```
# kubectl get deployment
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
mytomcat   1/1     1            1           36m

# kubectl delete -n default deployment mytomcat
deployment.apps "mytomcat" deleted

# kubectl get pod
No resources found in default namespace
```
`-n`: 指定namespace。不指定的话是default。

# 原因

对kubernates对象理解欠缺。
spec是必需的，它描述了对象的期望状态（Desired State）。
status描述了对象的 实际状态（Actual State） ，它是由 Kubernetes 系统提供和更新的。
一旦创建对象，Kubernetes 系统将持续工作以确保对象存在。

后来发现更好的方式是使用更新spec，让k8s自动更新pod。
```
kubectl edit -f xxx.yml

kubectl apply -f xxx.yml
```