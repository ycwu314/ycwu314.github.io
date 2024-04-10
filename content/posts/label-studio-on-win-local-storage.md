---
title: "Label Studio在windows上接入本地存储"
date: 2024-04-10T10:20:46+08:00
tags: ["AI"]
categories: ["AI"]
description: conda配置环境变量。
---

最近用label studio打标签炼丹，有些数据在本地硬盘，不想走s3或者再上传一次，于是使用local storage方式接入。但遇到了奇怪的问题，记录下。


# 安装 label studio

```
conda create --name label-studio
conda activate label-studio
conda install psycopg2  # required for LS 1.7.2 only
pip install label-studio

# 启动
label-studio start -p 8080 --data-dir d:\\label-studio-data
```

# 配置local storage

根据官网配置： https://labelstud.io/guide/storage#Local-storage

1. 环境变量

```bash
LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=/home/user (or LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=C:\\data\\media for Windows)
```

win在系统变量设置了。

2. 配置路径

path要配置为`绝对路径`。

经过测试，对于win，使用`c:\\`或者`c:\`或者`c:/`格式的分隔符都是ok的。

3. `Treats every bucket object as a source file`

开启。否则要手动通过json文件配置要导入的任务。

# 遇到问题

点击`sync`之后，顺利扫描到文件。

但是进入导入任务，发现图片无法打开。


>There was an issue loading URL from $image_url value
>
>Things to look out for:
>
>URL is valid
>URL scheme matches the service scheme, i.e. https and https
>The static server has wide-open CORS, more on that here
>Technical description:
>URL: /data/local-files/?d=cats-and-dogs%5Cimages%5CCats_Test0.png



根据文档，`/data/local-files/?d=`是label studio访问本地资源的api。`d=`后面跟着的是相对路径（相对于`LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT`）。

前人有多个有类似的问题：
- https://github.com/HumanSignal/label-studio/issues/2086

最初以为是python转换win路径问题，尝试了几种写法都不行。


直到搜索到这篇文章： [针对 anaconda 启动的 label-studio 本地项目设置基于 anaconda 环境的环境变量](https://www.ruan-cat.com/ruan-cat-own-notes/python/label-studio/label-studio.html#%E9%92%88%E5%AF%B9-anaconda-%E5%90%AF%E5%8A%A8%E7%9A%84-label-studio-%E6%9C%AC%E5%9C%B0%E9%A1%B9%E7%9B%AE%E8%AE%BE%E7%BD%AE%E5%9F%BA%E4%BA%8E-anaconda-%E7%8E%AF%E5%A2%83%E7%9A%84%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F)

想起之前是通过win系统属性配置全局环境变量，虽然在conda shell `echo %xx%`能识别出来，本地存储sync也能发现图片。但是本着试一下的心态
```
conda env config vars set LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
conda env config vars set LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=d:\\dataset
conda activate label-studio
```

然后发现图片正常能够加载了。

