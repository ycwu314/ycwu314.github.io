---
title: "Yolo 安装"
date: 2024-04-25T15:24:20+08:00
tags: ["AI"]
categories: ["AI"]
description: 
---

YOLOv8 是一个支持多种计算机视觉任务的人工智能框架。该框架可用于执行检测、分割、obb、分类和姿态估计。


# 安装 

```sh
# python >= 3.8
conda create -n yolo python=3.8 -y
conda activate yolo
conda install -c conda-forge ultralytics -y

# https://pytorch.org/get-started/previous-versions/
# change by gpu or cpu version
conda install pytorch==2.2.1 torchvision==0.17.1 torchaudio==2.2.1 cpuonly -c pytorch -y

```

# 使用

可以python代码或者CLI模式。

```
yolo TASK MODE ARGS

Where   TASK (optional) is one of [detect, segment, classify]
        MODE (required) is one of [train, val, predict, export, track]
        ARGS (optional) are any number of custom 'arg=value' pairs like 'imgsz=320' that override defaults.
```


# 参考

- 官网quickstart： https://docs.ultralytics.com/quickstart


