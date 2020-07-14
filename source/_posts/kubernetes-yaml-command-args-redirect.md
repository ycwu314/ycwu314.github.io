---
title: kubernetes yaml中command重定向的写法
date: 2019-10-07 23:06:18
tags: [kubernetes, 技巧]
categories: [kubernetes]
keywords: [kubernetes command redirect, kubernetes command 重定向]
description: kubernetes解析yaml文件的command和args有问题，不支持重定向操作符。需要使用`sh -c <command args>`方式替代。
---

在init container的实验中，通过echo重定向方式创建文件并且写入内容。
<!-- more -->
最初的版本是这样的：
```yml
spec:
  ...
  initContainers:
  - name: install
    image: busybox
    command: ["echo", "hello world", ">", "/work-dir/index.html"]
```
init container执行返回，但是进入容器后，并没有发现指定index.html文件。

然后换了另一种写法：
```yml
spec:
  ...
  initContainers:
  - name: install
    image: busybox
    command: ["echo"]
    args: ["hello world", ">", "/work-dir/index.html"]
```
还是不行。
换另一个命令，成功创建文件：
```yml
spec:
  ...
  initContainers:
  - name: install
    image: busybox
    command: ["touch", "/work-dir/index.html"]
```
于是怀疑是`>`的问题。采用字符串方式传入整个命令。
```yml
spec:
  ...
  initContainers:
  - name: install
    image: busybox
    command: ["/bin/sh", "-c", "echo hello world > /work-dir/index.html"]
```
上述命令表示以sh作为shell，`-c`参数后面是完整的命令行。
成功创建文件。

结论：
- k8s对命令行的重定向解析貌似有问题。使用`sh -c <command args>`代替。



