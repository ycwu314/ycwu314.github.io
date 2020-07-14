---
title: kubernetes的label和annotation
date: 2019-10-25 18:35:12
tags: [kubernetes]
categories: [kubernetes]
keywords: [kubernetes label, kubernetes annotation]
description: Label和Annotation都可以把扩展数据附加到Kubernetes资源对象，从而方便微服务的管理。
---

Label和Annotation都可以把扩展数据附加到Kubernetes资源对象，从而方便微服务的管理。Label主要用于选择对象。Annotation不能用于选择对象。
<!-- more -->
# label

Label主要用于选择对象。

Label key的组成：
- 不得超过63个字符
- 可以使用前缀，使用/分隔，前缀必须是DNS子域，不得超过253个字符，系统中的自动化组件创建的label必须指定前缀，kubernetes.io/由kubernetes保留
起始必须是字母（大小写都可以）或数字，中间可以有连字符、下划线和点

Label value的组成：
- 不得超过63个字符
- 起始必须是字母（大小写都可以）或数字，中间可以有连字符、下划线和点

Label selector有两种类型：
- equality-based ：可以使用`=`、`==`、`!=`操作符，可以使用逗号分隔多个表达式
- set-based ：可以使用`in`、`notin`、`!`操作符，另外还可以没有操作符，直接写出某个label的key，表示过滤有某个key的object而不管该key的value是何值，`!`表示没有该label的object

# annotation

Annotation不能用于标识及选择对象，annotation中的元数据可多可少，可以是结构化的或非结构化的，也可以包含label中不允许出现的字符。
一些可以记录在 annotation ：
- 声明配置层管理的字段
- 创建信息、版本信息或镜像信息
- 用户信息，以及工具或系统来源信息

使用annotation，方便创建用于部署、管理、内部检查的共享工具和客户端库。

# label实战


为节点添加label
```
# kubectl label node izwz9h8m2chowowqckbcy0z env=dev
node/izwz9h8m2chowowqckbcy0z labeled
```

覆盖已有label，要添加`--overwrite`选项，否则报错
```
# kubectl label node izwz9h8m2chowowqckbcy0z env=dev
error: 'env' already has a value (dev), and --overwrite is false

# kubectl label node izwz9h8m2chowowqckbcy0z env=test --overwrite
node/izwz9h8m2chowowqckbcy0z labeled
```


查看lable
```
# kubectl get node --show-labels
NAME                      STATUS   ROLES    AGE   VERSION   LABELS
izwz9h8m2chowowqckbcy0z   Ready    <none>   19d   v1.16.2   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,env=dev,kubernetes.io/arch=amd64,kubernetes.io/hostname=izwz9h8m2chowowqckbcy0z,kubernetes.io/os=linux,microk8s.io/cluster=true
```

删除label，在key后面增加`-`即可
```
# kubectl label node izwz9h8m2chowowqckbcy0z env-
node/izwz9h8m2chowowqckbcy0z labeled
```

使用label过滤
```
# kubectl get node --show-labels -l env=dev
No resources found in default namespace.

# kubectl label node izwz9h8m2chowowqckbcy0z env=dev
node/izwz9h8m2chowowqckbcy0z labeled

# kubectl get node --show-labels -l env=dev
NAME                      STATUS   ROLES    AGE   VERSION   LABELS
izwz9h8m2chowowqckbcy0z   Ready    <none>   19d   v1.16.2   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,env=dev,kubernetes.io/arch=amd64,kubernetes.io/hostname=izwz9h8m2chowowqckbcy0z,kubernetes.io/os=linux,microk8s.io/cluster=true
```

上面提到label支持集合操作。过滤env是dev或者test的node
```
# kubectl get node --show-labels -l 'env in (dev,test)'
```

# annotation实战

annotation的操作和label类似。

添加annotation
```
# kubectl annotate node izwz9h8m2chowowqckbcy0z admin=ycwu
```

查看annotation
```
# kubectl get node izwz9h8m2chowowqckbcy0z -o yaml | less
```
```yaml
apiVersion: v1
kind: Node
metadata:
  annotations:
    admim: ycwu
    node.alpha.kubernetes.io/ttl: "0"
    volumes.kubernetes.io/controller-managed-attach-detach: "true"
  creationTimestamp: "2019-10-07T05:33:04Z"
# 以下省略
```

删除annotation
```
# kubectl annotate node izwz9h8m2chowowqckbcy0z admin-
node/izwz9h8m2chowowqckbcy0z annotated
```

# 小结

Kubernetes对labels进行索引和反向索引用来优化查询和watch。
不要在label中使用大型、非标识的结构化数据，记录这样的数据应该用annotation。



