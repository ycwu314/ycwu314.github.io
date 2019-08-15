---
title: html链接rel属性介绍：external nofollow noreferer noopener
date: 2019-08-15 12:17:39
tags: [html, 网路安全, 技巧]
categories: [html]
keywords: [target _blank, rel nofollow, rel noreferer, rel noopener, rel external, hexo nofollow]
description: target="_blank"在新窗口中打开链接。rel external表明这是个外部链接。rel noreferer会不发送当前站点地址作为referer。rel nofollow告诉爬虫不要跟踪这个链接。rel noopener表示在新的进程中打开页面，提高性能和解决安全隐患。hexo-autonofollow插件做外链优化。
---

# 背景

rel字段用于描述链接和当前URL的关系。
学习seo的时候，发现链接的rel字段有几个属性，记录下来。

{% asset_img insertlink.gif %}

# external

告诉爬虫这是一个外部链接。标准的html doctype写法。效果等同于`target="_blank"`。

# nofollow

`nofollow`告诉爬虫不要跟踪这个链接，不会分享pagerank权重。
最初由google提出，用于解决垃圾链接。比如热门站点留言区发一条留言指向自己的网站（从热门站点产生了外链到不知名站点）。

# noreferer

`noreferer`告诉浏览器，打开该链接时不发送当前站点路径作为referer字段。在html规范中，referer字段用于来源跟踪。因此，使用`noreferer`能够提高打开外链时的隐私安全。

# noopener

在新窗口打开链接，通常的写法
```html
<a href="example.com" target="_blank">
```
然而，这样有很大的安全和性能隐患！

引用google developers上的文章：[网站使用 rel="noopener" 打开外部锚](https://developers.google.com/web/tools/lighthouse/audits/noopener)
>当您的页面链接至使用 target="_blank" 的另一个页面时，新页面将与您的页面在同一个进程上运行。 如果新页面正在执行开销极大的 JavaScript，您的页面性能可能会受影响。
>
>此外，target="_blank" 也是一个安全漏洞。新的页面可以通过 window.opener 访问您的窗口对象，并且它可以使用 window.opener.location = newURL 将您的页面导航至不同的网址。

这篇文章讲到`noopener`的好处：[The performance benefits of rel=noopener](https://jakearchibald.com/2016/performance-benefits-of-rel-noopener/)
>However, due to the synchronous cross-window access the DOM gives us via window.opener, windows launched via target="_blank" end up in the same process & thread. The same is true for iframes and windows opened via window.open.
>
>rel="noopener" prevents window.opener, so there's no cross-window access. Chromium browsers optimise for this and open the new page in its own process.

`noopener`使得外部链接在独立的进程中打开。新窗口`window.opener`会为null。

# 实践

1. 使用`hexo-autonofollow`插件
```
npm install hexo-autonofollow --save
```
也有另一个插件`hexo-nofollow`，但是截至2019.8.15，这个插件的html转义有问题，如果结合neat-html就会报错。因此使用`hexo-autonofollow`。

2. 修改项目的`_config.yml`
```yml
nofollow:
  enable: true
  exclude:
    - 'ycwu314.github.io'
    - 'ycwu314.gitee.io'
```

3. 查看生成的链接
```html
<a href="https://developers.google.com/web/tools/lighthouse/audits/noopener" rel="external nofollow noopener noreferrer" target="_blank">网站使用 rel=”noopener” 打开外部锚</a>
```
