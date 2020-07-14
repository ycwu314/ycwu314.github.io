---
title: kubernates 资源限制
date: 2020-01-16 11:05:18
tags: [kubernates]
categories: [kubernates]
keywords: [kubernates 资源限制]
description: kubernates 资源单位和限制方式。
---

# 资源单位

## cpu单位

1个k8s cpu对应
- 1 AWS vCPU
- 1 GCP Core
- 1 Azure vCore
- 1 Hyperthread on a bare-metal Intel processor with Hyperthreading

<!-- more -->

cpu也可以是小数。1000m=1。`500m =  0.5 cpu`。

## 存储单位

以byte作为单位。直接的数字代表Byte。
当然有更大的单位：
- E，P，T，G，M，K
- Ei，Pi，Ti ，Gi，Mi，Ki

`i`后缀表示1024，非`i`后缀表示1000。
例如：
- 1K = 1000 Byte
- 1Ki = 1024 Byte

# 资源限制

资源限制可以在pod级别，也可以在namespace级别。

pod级别
- spec.containers[].resources.limits.cpu
- spec.containers[].resources.limits.memory
- spec.containers[].resources.requests.cpu
- spec.containers[].resources.requests.memory

namespace级别
- spec.limits[].default.cpu，default limit
- spec.limits[].default.memory，同上
- spec.limits[].defaultRequest.cpu，default request
- spec.limits[].defaultRequest.memory，同上

pod的设置优先级高于namespace。

