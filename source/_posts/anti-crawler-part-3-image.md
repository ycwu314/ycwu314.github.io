---
title: 反爬虫系列之3：图片保护
date: 2019-09-01 10:42:12
tags: [爬虫]
categories: [爬虫]
keywords: [图片防爬, hexo-lazyload-image, hexo open graph]
description: 保护图片的方式：1. 水印； 2. cdn referer防盗链； 3. hexo-lazyload-image懒加载图片插件
---

# 图片保护

上次讲到使用字体反爬保护文章文本内容。文章上还有图片资源需要保护。
这些爬虫站点爬图片的效果：
{% asset_img v1_你可能是爬虫文章的受害者.webp 你可能是爬虫文章的受害者 %}
那个大大的loading位置，其实是一张图。显然爬虫没有拿到真实的图片。

文章爬虫站点通常会直接读取img标签的src属性，获取图片url。有的会转存到自己的存储，避免图片失效。但这会增加存储和带宽成本，因此很多爬虫站点会直接使用原站的图片地址，消耗原站的带宽资源。

<!-- more -->

图片保护的方式有：
- 水印
- 防盗链
- 保护图片链接

# 给图片打水印

水印有2种，明水印和盲水印。
明水印是肉眼可见的水印。随着抠图工具越来越智能，明水印的保护作用也变低。
盲水印，也叫数字水印，是把水印信息写入到图片的高频区域，肉眼不可见，也对原图片不产生明显的质量下降，即使被编辑（加滤镜效果），还能保留。需要用特殊方法提取。
明水印是基础的，数字水印以后我再专门展开。
这是我加水印的命令，需要安装imagemagick工具
```bash
ls *.png *.PNG *.webp *.gif *.jpg -1 | xargs  -i convert "{}" ( -size 150x -background none -fill grey -pointsize 16 -gravity center label:"ycwu314.github.io" -trim -rotate -30 -bordercolor none -border 30 -write mpr:wm +delete +clone -fill mpr:wm  -draw "color 0,0 reset" ) -compose over -composite "{}"
```
替换label文本即可。注意：直接覆盖原图！把图片复制到另一个文件操作。
（ps. 大写PNG后缀是windows自带截图工具的后缀名）
这个脚本并不完美，没有考虑背景色，还有图片尺寸的问题。对于长条形状或者背景色很深（intellij的截图），手动打水印。另外，加上水印图片尺寸变大，要再拖到tinypng压缩，或者转换为webp。

# cdn图片防盗链

如果有图片cdn，那么可以在cdn上配置简单的防盗链。常见的图片防盗链方式是检查referer字段。
假设xxx站点爬了我的图片链接，浏览器打开页面，如果不做特殊处理，那么发出图片请求的referer是xxx站点、而非cdn允许的站点referer，那么cdn可以直接拒绝请求。
但是我的小站目前没有使用图片cdn，因为国内cdn提供商都要求备案了。另外还要插件支持，不然写作体验不好。


# hexo-lazyload-image 保护图片链接

保护图片链接是另一个手段。既然爬虫直接保存img标签的src属性，那么src属性就放一个假的地址，然后通过js增加一个事件，把真实图片加载回去。
上面loading截图也正是这个原理。
之前使用了hexo-lazyload-image插件实现图片懒加载，会把src属性替换掉。默认图片是loading图片，并且通过data:image方式直接写到html文件里面。
默认图片base64编码大概3KB，每多一个图片，html文件大小就要增加3KB，显然不太合适。
更好的做法是自定义图片，并且保存在图床。

hexo项目_config.yml配置
```yml
lazyload:
  enable: true 
  onlypost: true
  loadingImg: <懒加载图片地址>
```

源码不复杂，把真实图片地址保存在图片的data-original属性。
```js
    return htmlContent.replace(/<img(\s*?)src="(.*?)"(.*?)>/gi, function (str, p1, p2) {
        // might be duplicate
        if(/data-original/gi.test(str)){
            return str;
        }
        return str.replace(p2, loadingImage + '" data-original="' + p2);
    });
```

加载的时候，注册scroll事件，新建图片对象并且从data-origina加载真正的图片。具体在`simple-lazyload.js`。

这是最新的效果：
![](https://s2.ax1x.com/2019/09/01/npDr38.png)

但是hexo-lazyload-image会导致hexo生成open graph标签生成图片信息不正确，图片都是懒加载的图：
```html
<meta property="og:image" content="https://s2.ax1x.com/2019/09/01/npDr38.png">
```

在hexo源码全文查找`og:image`，最后定位到这个文件：hexo/lib/plugins/helper/open_graph.js
原来只读取src属性
```js
$('img').each(function() {
  const src = $(this).attr('src');
  if (src) images.push(src);
});
```
改为优先使用data-original属性
```js
$('img').each(function() {
  // hexo-lazyload-image plugin
  const original = $(this).attr('data-original');
  if(original) {
    images.push(original);
  } else {
    const src = $(this).attr('src');
    if (src) images.push(src);
  }
});
```
最终效果
```html
<meta property="og:image" content="https://ycwu314.github.io/p/anti-crawler-part-3-image/你可能是爬虫文章的受害者.webp">
```
由于修改了hexo框架，因此在travis ci增加更新open_graph.js动作
```yml
script:
  - rm -f node_modules/hexo/lib/plugins/helper/open_graph.js 
  - cp .travis/open_graph.js node_modules/hexo/lib/plugins/helper/
```