---
title: chrome不同方式查看cookies的坑
date: 2020-05-18 10:26:11
tags: [chrome, 故障案例]
categories: [web]
keywords: [chrome cookies]
description: 查看方式不同，导致的cookies“不见了”。
---

# 背景

前后端联调cas系统，前端应该写入TGC cookies，但是说有时候没有写入成功，没有查看到对应的cookies。
扯来扯去，发现是chrome中不同查看cookies的方式导致。
需要区分的是：
- 本次页面设置的cookies，以及站点存储cookies。
- 页面刷新之后，当前cookies可能变化
<!-- more -->

# 方式1：地址栏查看cookies

“查看网页时设置”：是当前页面写入的cookies。
对于同一个网页，如果第一次访问写入cookies，那么**刷新**当前页面，显示的cookies可能变少，有可能产生误解（cookies丢失、写入失败）。

# 方式2：debug console查看cookies

这里查看的是当前页面使用到的cookies。


# 方式3：chrome://settings/siteData 查看cookies

```
chrome://settings/siteData
```

站点级别存储的cookies，不受刷新影响。

# 例子

清空站点cookies，再进行实验。


1. 打开网页，登录成功后：（这里接入了cas）

地址栏方式：
{% asset_img address-bar.png address-bar %}

debug console：
{% asset_img debug-console.png debug-console %}

siteData：
{% asset_img siteData.png siteData %}

2. 点击页面刷新之后

地址栏方式：
{% asset_img address-bar-refreshed.png address-bar-refreshed %}

debug console：
{% asset_img debug-console-refreshed.png debug-console-refreshed %}


siteData（不变）：
{% asset_img siteData.png siteData %}

# 回到案例

前端、现场习惯使用地址栏、debug console观察cookies，因此看到的是本次页面所写入的cookies。
会有一种错觉，cas的TGC cookies丢失了。

后端习惯在siteData看cookies，因此看到cookies正确写入。

结论：
- 以后统一在siteData查看cookies（调试当前页面写入cookies的除外）。

