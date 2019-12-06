---
title: 小程序开发者工具杂锦case
date: 2019-12-06 15:39:35
tags: [小程序]
categories: [小程序]
keywords: [小程序 sitemap, 小程序 wx:key performance]
description: 小程序开发者工具黄色提示实在太烦人了。
---

上次倒腾仿网易云音乐小程序，发现后端接口组装接口略为复杂，算了，换个demo继续搞。
只是导入开发者工具，一堆黄色提示，烦人，于是整理一下。
<!-- more -->

# sitemap

>根据 sitemap 的规则[0]，当前页面 [pages/index/index] 将被索引

网站上的sitemap是站点地图，方便搜索引擎爬取页面。小程序的sitemap作用也是一样的。
当开发者允许微信索引时，微信会通过爬虫的形式，为小程序的页面内容建立索引。当用户的搜索词条触发该索引时，小程序的页面将可能展示在搜索结果中。 爬虫访问小程序内页面时，会携带特定的 `user-agent：mpcrawler` 及`场景值：1129`。

开发者工具关闭sitemap提示的方式：
>sitemap 的索引提示是默认开启的，如需要关闭 sitemap 的索引提示，可在小程序项目配置文件 project.config.json 的 setting 中配置字段 checkSiteMap 为 false

# wx:key

>Now you can provide attr `wx:key` for a `wx:for` to improve performance.

根据[列表渲染](https://developers.weixin.qq.com/miniprogram/dev/reference/wxml/list.html)描述：

如果列表中项目的位置会动态改变或者有新的项目添加到列表中，并且希望列表中的项目保持自己的特征和状态（如 input 中的输入内容，switch 的选中状态），需要使用 wx:key 来指定列表中项目的唯一的标识符。
**当数据改变触发渲染层重新渲染的时候，会校正带有 key 的组件，框架会确保他们被重新排序，而不是重新创建，以确保使组件保持自身的状态，并且提高列表渲染时的效率。**
如不提供 wx:key，会报一个 warning， 如果明确知道该列表是静态，或者不必关注其顺序，可以选择忽略。

# cover-view 和 canvas

```
<cover-view/> 内只能嵌套 <cover-view/> <cover-image/> <button/> <navigator/> <ad/>，canvas 标签的子节点树在真机上都会被忽略。
```

cover-view能覆盖在原生组件 map、video、canvas、camera 之上，且只能嵌套特定标签。
通常可以用来做弹窗。
导入的demo在cover-view内嵌套canvas，导致提示。注释掉即可。