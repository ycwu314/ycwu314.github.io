---
title: kubernates yaml文件工具
date: 2019-09-29 17:35:03
tags: [kubernates]
categories: [kubernates]
keywords: [kubernates yaml export, kubectl --dry-run]
description: kubernates yaml文件工具。
---

kubernates推荐使用yaml文件定义对象，而非直接使用kubectl执行定义create/run命令。
<!-- more -->
# 导出已有资源的yaml

`kubectl get <resource-type> <resource> --export -o yaml`以yaml格式导出系统中已有资源描述。
```
# kubectl get pod mytomcat-7d68ffdbfb-xjcz4 --export  -o yaml > mytomcat.yml
Flag --export has been deprecated, This flag is deprecated and will be removed in future.
```
注意，未来版本的kubernates会去掉`--export`参数。[这里](https://github.com/kubernetes/kubernetes/pull/73787)有相关的争论，感兴趣可以阅读。

如果没有`--export`参数，那么get资源会显示status相关的输出，对于定义kubernates对象来说是多余的。

# `--dry-run`

`--dry-run`仅打印这个对象，而不会执行命令。
```
# kubectl run  mytomcat --image=tomcat --port=8080 --generator=run-pod/v1  --replicas=2  --dry-run -o yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: null
  labels:
    run: mytomcat
  name: mytomcat
spec:
  containers:
  - image: tomcat
    name: mytomcat
    ports:
    - containerPort: 8080
    resources: {}
  dnsPolicy: ClusterFirst
  restartPolicy: Always
status: {}
```

# kompose

Kompose是Kubernetes社区开发的一个转换工具，可以方便地将简单的Docker Compose模板转化成为Kubernetes的Yaml描述文件，并在Kubernetes集群上部署和管理应用。

由于已经跳过docker compose阶段，以后有需要再尝试这个工具。

# yaml文件常见错误

>error: yaml: line 2: mapping values are not allowed in this context

`key: value`，注意在value和“:"之间要有一个空格。

>error: yaml: line 3: found character that cannot start any token

YAML文件里面不能出现tab键。