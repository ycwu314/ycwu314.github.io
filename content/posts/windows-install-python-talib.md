---
title: "Windows Install Python TA-Lib"
date: 2025-02-12T11:36:24+08:00
tags: ["AI"]
categories: ["AI"]
description: TA-Lib (Technical Analysis Library) 是一个广泛使用的开源 Python 库，主要用于金融市场技术分析。
---

TA-Lib (Technical Analysis Library) 是一个广泛使用的开源 Python 库，主要用于金融市场技术分析。它提供 150 多种技术指标和工具。

TA-Lib的实现是依赖平台的，在Windows上直接使用pip安装会有问题。通常有2种方法解决：
1. 安装visual studio编译TA-Lib
2. 使用别人预先编译的二进制文件（更加方便）


解决：
1. [talib-build](https://github.com/cgohlke/talib-build) 下载对应平台、架构的wheel文件。
2. 使用pip安装。

```
pip install ta_lib-0.6.3-cp312-cp312-win_amd64.whl
```