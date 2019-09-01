---
title: 修改hexo图片title位置
date: 2019-09-01 19:50:47
tags: [技巧, hexo]
categories: [hexo]
keywords: [hexo image title, image-caption, hexo 图片 title]
description: 默认的hexo图片title属性上浮在图片底部，导致看不清楚。修改image-caption的css配置，使其下浮在图片下面。
---

# hexo图片title样式

hexo插入图片的语法
```
{% asset_img slug [title] %}
```
展现效果是title字段浮到图片上面，导致看不清楚。
{% asset_img hexo-image-position.webp hexo图片默认效果 %}
<!-- more -->
查看生成的代码
```html
<a class="fancybox fancybox.image" href="/p/anti-crawler-part-3-image/你可能是爬虫文章的受害者.webp" itemscope="" itemtype="http://schema.org/ImageObject" itemprop="url" data-fancybox="default" rel="default" title="你可能是爬虫文章的受害者" data-caption="你可能是爬虫文章的受害者"><img src="/p/anti-crawler-part-3-image/你可能是爬虫文章的受害者.webp" data-original="/p/anti-crawler-part-3-image/你可能是爬虫文章的受害者.webp" title="你可能是爬虫文章的受害者">
    <p class="image-caption">你可能是爬虫文章的受害者</p>
</a>
```
发现文字由image-caption控制样式。
全文查找hexo、next的源码，最后定位到这个文件：
`themes\next\source\css\_common\components\post\post.styl`
```css
.post-body .image-caption,
.post-body .figure .caption {
  margin: -20px auto 15px;
  text-align: center;
  font-size: $font-size-base;
  color: $grey-dark;
  font-weight: bold;
  line-height: 1;
}
```
默认是上浮20px，修改为：
```css
margin: 20px auto 15px;
```
这样文字就不会挡住图片了。



