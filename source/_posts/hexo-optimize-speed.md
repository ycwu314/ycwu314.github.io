---
title: hexo页面优化
date: 2019-08-07 20:17:38
tags: [hexo, 技巧, web]
categories: [hexo]
keywords: [hexo优化, 页面优化]
description:
---

博客打开有点慢，于是做优化。页面优化工具使用[PageSpeed Insights](https://developers.google.com/speed/pagespeed/insights/)。

# 思路

优化web页面的常见思路
- 压缩文本、图片等资源
- 静态资源使用cdn
- 合并js、css文件，把多个请求资源请求合并为一个
- 设置适当的静态资源缓存时间
- 资源懒加载
- 优化资源加载顺序

# 图片优化

## 文章图片

平时文章的图片都是png格式，并且使用tinypng.com优化过，因此除非改为webp，否则优化空间不大。
一旦改了图片格式，还要修改md文件，需要写脚本实现。目前来说产出投入比不高。以后有空再搞。

## 背景图

原来的背景图网上找来的，很大，1.6MB，即使使用cdn加载也要快1s。是优化的首要对象。查看背景图，大小是`4096 x 2315`，支持4K。。。但是目前4K未普及，直接缩小50%的尺寸！
这里安利一个在线图片工具，https://squoosh.app/ ，有多种格式、算法、参数可以选择。
最终的jpg是87KB，如果转换webp，可以缩小到56KB。但是路过图床不支持webp格式，于是选择输出png，再保存到图床。

**优化效果：背景图大小从1.6MB变为87KB。**

## avatar

头像是从微信复制过来的。尺寸`960 x 960`，大小105KB。对于头像来说，实在太大。缩放大小，再转换webp格式，8KB不到。
**优化效果：头像大小从105KB变为8KB。**

## 图片懒加载

首页文章比较多，默认下载所有图片，导致加载瀑布时间变长。理想的情况是，只加载前面的图片，往下滚动再加载新的图片、或者在空闲时自动加载图片，实现图片的懒加载。
这里使用的`hexo-lazyload-image`
```s
npm install hexo-lazyload-image --save
```
然后在项目的`_config.yml`增加配置
```yml
lazyload:
  enable: true 
  onlypost: false
  loadingImg: # eg ./images/loading.gif 
```
**优化效果：首页图片加载数量减少一半以上。**

但是这个插件有不足，滚动之后自动加载图片比较慢。。。通常要1到3秒才显示。

# 内容压缩

hexo默认生成的html，有很多空行和空格。
{% asset_img 文章未压缩.png %}
默认带的css、js也是存在压缩的空间。这里使用`hexo-neat`插件
```js
npm install hexo-neat --save
```
然后在项目的`_config.yml`增加配置
```yml
# 文件压缩，设置一些需要跳过的文件 
# hexo-neat
neat_enable: true
# 压缩 html
neat_html:
  enable: true
  exclude:
# 压缩 css
neat_css:
  enable: true
  exclude:
    - '**/*.min.css'
# 压缩 js
neat_js:
  enable: true
  mangle: true
  output:
  compress:
  exclude:
    - '**/*.min.js'
    - '**/index.js'
```
注意要跳过一些已经压缩了的文件。另外，不要忽略`swig`、`md`文件。安装hexo-neat之后，`hexo g`会自动压缩文件，时间变长
{% asset_img hexo-neat压缩.png %}

**优化效果：文章大小减少1/3以上。**

# cdn优化

默认从站点加载css、js资源。其实hexo next提供了jquery、fancybox等库的cdn路径。具体在next的`_config.yml`查找就是了。
next默认提供的有cloudfare、jsdelivr，感觉cloudfare要快些。

从加载路径发现统计访问人数的不蒜子`https://busuanzi.ibruce.info/`的js文件没有做缓存。网上找到一个js的cdn路径`https://cdn.jsdelivr.net/npm/busuanzi@2.3.0/bsz.pure.mini.js`，修改文件在`\themes\next\layout\_third-party\analytics\busuanzi-counter.swig`。

{% asset_img 缓存策略.png %}
另外发现github pages的静态资源缓存时间是10min。

**优化效果：公共基础库从cdn下载，减少五六个http请求**

# 字体优化

>利用 font-display 这项 CSS 功能，确保文本在网页字体加载期间始终对用户可见。
{% asset_img fontawesome.png %}
这个不知道怎么优化，以后再研究。


# 优化效果

{% asset_img desktop.png %}
速度明显比以前快了😄
