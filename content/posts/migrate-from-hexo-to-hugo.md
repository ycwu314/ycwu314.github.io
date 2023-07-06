---
title: 从hexo迁移到hugo
date: 2023-07-04T18:10:34+08:00
description: hexo构建慢、在电脑间迁移麻烦，换成hugo了。
---

# 为什么迁移

- hexo构建太慢。现在博客hexo构建一次要几十秒。对比hugo只要2秒不到。
- hexo在不同电脑间迁移成本高。hexo基于nodejs体系，需要安装nodejs环境，下载一大堆依赖包，如果出现版本冲突，还要手动修改node_modules的源文件，非常麻烦。而hugo只需要下载一个二进制包即可，非常方便。


# hugo版本问题

下载主题后，提示sass报错

```
Error: Error building site: TOCSS: failed to transform "style.scss" (text/x-scss). Check your Hugo installation; you need the extended version to build SCSS/SASS with transpiler set to 'libsass'.: this feature is not available in your current Hugo version, see https://goo.gl/YMrWcn for more information
```

看官网介绍：
https://gohugo.io/installation/linux/

```
Hugo is available in two editions: standard and extended. With the extended edition you can:

Encode to the WebP format when processing images. You can decode WebP images with either edition.
Transpile Sass to CSS using the embedded LibSass transpiler. The extended edition is not required to use the Dart Sass transpiler.
We recommend that you install the extended edition.
```


解决：下载带extended的文件即可。


# 标签写法


```
ERROR render of "page" failed: "D:\hugo\justnft.eu.org\themes\hugo-theme-stack\layouts\_default\baseof.html:4:12": execute of template failed: template: _default/single.html:4:12: executing "_default/single.html" at <partial "head/head.html" .>: error calling partial: "D:\hugo\justnft.eu.org\themes\hugo-theme-stack\layouts\partials\head\head.html:15:4": execute of template failed: template: partials/head/head.html:15:4: executing "partials/head/head.html" at <partial "head/opengraph/include.html" .>: error calling partial: "D:\hugo\justnft.eu.org\themes\hugo-theme-stack\layouts\partials\head\opengraph\include.html:1:3": execute of template failed: template: partials/head/opengraph/include.html:1:3: executing "partials/head/opengraph/include.html" at <partial "head/opengraph/provider/base" .>: error calling partial: "D:\hugo\justnft.eu.org\themes\hugo-theme-stack\layouts\partials\head\opengraph\provider\base.html:22:21": execute of template failed: template: partials/head/opengraph/provider/base.html:22:21: executing "partials/head/opengraph/provider/base.html" at <.Params.tags>: range can't iterate over devops
```

解决：标签内容用数组包围
```
tags: [devops]
categories: [devops]
```

# 文章链接

hexo的文章链接语法：
```
{% post_link anti-crawler-part-1 %}
```
修改为
```
[anti-crawler-part-1](/posts/anti-crawler-part-1)
```

```
sed -ri "s#\{% post_link (.*) %\}#[\1](/posts/\1)#g" *.md
```
缺点是没有使用被链接文章的标题。

# 图片

## 图片存放方式

hugo图片存放的方式：
1. 图床
2. static目录
3. 在posts中创建文章目录，保存图片

考虑：
1. 图床不可控，而且编辑器要装插件支持自动上传和获取路径，电脑迁移比较麻烦。
2. 丢到static目录，最简单，不过图片多了看着不舒服。
3. 放到文章目录，和之前hexo使用习惯一致。


于是使用方案3。`hugo new posts/<文章目录>/index.md`。其中index.md是文章内容。
```
├─api-gateway-p1-kong-konga-install
│      index.md
│      kong-db.png
│      konga-db.png
│      konga-new-connection.png
```

需要把原来hexo文章移动到同名目录，并且重命名。
```
ls -d */ | tr -d '/' | xargs -i mv {}.md {}/

ls -d */ | tr -d '/' | xargs -i mv {}/{}.md {}/index.md
```


## 图片标签改造

hexo的图片语法
```
-- 带alt提示
{% asset_img ssh转发.png ssh转发 %}

-- 不带alt提示
{% asset_img ssh转发.png %}
```

hugo的图片语法是标准md的`![]()`。因此要全文替换。

思路：使用sed的正则分组匹配能力，提取图片文件名。
- `-r`: 使用正则扩展模式
- `\1`: 第一个分组匹配

```
sed -ri "s/\{% asset_img (.*\.png)(.*) %\}/\![\1](\1)/g" *.md
sed -ri "s/\{% asset_img (.*\.jpg)(.*) %\}/\![\1](\1)/g" *.md
sed -ri "s/\{% asset_img (.*\.gif)(.*) %\}/\![\1](\1)/g" *.md
sed -ri "s/\{% asset_img (.*\.webp)(.*) %\}/\![\1](\1)/g" *.md
sed -ri "s/\{% asset_img (.*\.PNG)(.*) %\}/\![\1](\1)/g" *.md
sed -ri "s/\{% asset_img (.*\.svg)(.*) %\}/\![\1](\1)/g" *.md
```

`grep asseet_img *.md`检查遗漏。

后来才发现挖了个小坑。



## 图片格式匹配

```
Error: error building site: "D:\hugo\justnft.eu.org\content\posts\network-arp\index.md:1:1": "D:\hugo\justnft.eu.org\themes\hugo-theme-stack\layouts\_default\_markup\render-image.html:21:23": execute of template failed: template: _default/_markup/render-image.html:21:23: executing "_default/_markup/render-image.html" at <$image.Resize>: error calling Resize: image "D:\\hugo\\justnft.eu.org\\content\\posts\\network-arp\\arp-state-machine.gif": resize : failed to decode gif: gif: can't recognize format "\x89PNG\r\n"
```
图片真实类型是png，但是文件名是gif，因此报错。
修改文件名即可。


## 图片和文本排版

hexo的asset_img图片插入了换行，所以没有在图片标签前后换行也不影响展示。
但是hugo的排版按照标准md渲染，图片前后没有换行会导致文本、图片连着一块。
这就是之前替换asset_img标签挖的小坑。

解决：
这个问题如果在替换asset_img时发现就很好解决。
现在需要在markdown图片标签前后加上换行。
sed命令可以在匹配行的前面（`/i`）和后面（`/a`）插入换行，注意转义。
```
# posts目录，这时候文章已经挪到各自目录下。

ls -d */ | tr -d '/' | xargs -i sed -i -e "/\!\[/i\\\n" -e "/\!\[/a\\\n" {}/index.md
```



