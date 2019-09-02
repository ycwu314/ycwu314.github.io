---
title: 反爬虫系列之2：字体反爬
date: 2019-08-31 18:09:59
tags: [爬虫, hexo]
categories: [爬虫]
keywords: [字体反爬, fonttools]
description: 字体反爬，把部分字符映射到uft8的自定义字符区间，并且生成一个字体文件，可以正常显示这些区间的字符。利用字符映射表，把原来的字符替换成新字符编码。自定义字体字符数量不能太多。
---

# 字体反爬介绍

上一篇文章
- {% post_link anti-crawler-part-1 %}

打开来看，显示如下
{% asset_img font-anti-crawler.png 字体反爬效果 %}

但是查看源码
```
&#xe177;&#xf74d;&#xe1ce;想做&#xe23f;小站&#xe3da;
```
在浏览器看内容好好的，但是源码却是一团乱七八糟的转码。
这就是反爬中经常使用的一个技巧：字体反爬。
<!-- more -->

# 字体反爬原理

字体文件是每个字符区域可视化的描述。现在基本是矢量字体，就是字符每个笔画的x、y坐标描述。  
页面采用了utf8编码。其中有一个自定义区域：`U+E000-F8FF`。  
把一些字符，比如数字、某些缺少了就会影响阅读理解的汉字（例如高、低、大、小）、一些关键符号（`>`、`<`），映射到这个区域，再替换原文的对应字符。  
可是正常人要怎么看呢？创造一种字体，能够显示这些自定义的字，比如`&#xe177;`。  
爬虫如果只爬了我的文章，却没有对应字体的话，那么显示就是一团乱七八糟。这样能够保护原有内容。  
字体反爬在小说站点上使用很久了。  
字体反爬的核心思路是对人友好，对爬虫不友好。还有另一种类似思路的方式：css content，以后有机会再介绍。

但是字体反爬不是silver bullet。
1. 可能对seo造成影响。搜索引擎爬虫原文章之后，会做文章质量打分。字体反爬产生了一堆计算机无法用语义模型去理解的内容，导致评分变低。
2. 为了显示这些字体，需要额外加载字体文件，影响页面性能。因此替换的字符是有讲究的，不是随便找。

字体反爬在实现上主要2种：
1. 只改变字符编码。例如，`我`的uft编码是`0x6211`，把它映射到`U+E000-F8FF`其中一个槽位。但是`我`字体每个笔画xy坐标不改变。这样最简单，只需修改映射即可。
2. 改变字符编码，同时改变笔画的xy坐标。真·创造字体了。

为什么要改变字体笔画呢？因为自造字体，通常会基于某个已有字体文件提取目标字符。虽然我不知道0xe177是什么，但是根据笔画xy坐标做映射，就可以反推过去这个原来是哪个字了。
如果给笔画xy坐标加上扰动，那么这个反推过程就不能直接通过反向映射实现。
此时的反字体反爬，就要使用机器学习方式，使用LR或者GAN方式识别，得到映射的码表。
当然，还有一种方式是用OCR，但是大规模爬取的话，呵呵。

# 实施字体反爬

对于我的静态站点，字体反爬是比较合适的。能够应付一堆爬虫站点，并且我的实施成本也低。
实施字体反爬，要解决的问题：
- 选择哪些字做替换
- 生成新的字体
- hexo怎样应用自定义字体
- 怎么在hexo生成静态html的时候做替换

# 选择要替换的字符

粗糙的做法是，把经常出现的字符替换掉。但这个做法真的很粗糙。因为排在前面的，肯定有“的”之类的字。
去掉的字要对理解产生困难，并且字数越少越好。字数太多，导致字体文件增大。特殊编码的字越多，对原文语义缺失越多，搜索引擎机器打分模型也会有影响。
第一版先做粗糙点，快速上线后再优化。
具体实现也简单，写一个python脚本，读取所有文章markdown，做个word count，再根据计数排序就ok了。
以后还可以针对每个文章自定义字体。

# 使用fonttools创建字体

接下来就给替换字符创造字体文件。
python上常用的字体工具是fonttools。
```
pip3 install fonttools
```
windows上有个好用的工具，"High-Logic FontCreator"，可以方便查看字体文件，测试的时候很方便，可以申请评估版使用。
我打算从windows上的某个字体作为基础。系统上有2种类型的字体文件：ttc，ttf：
- ttf是单个true type字体的文件。
- ttc包含多个true type字体。

有些字体大部分字符相同，但是个别字形不同，使用ttc方式存储，可以共享相同编码的字符，节省字体文件存储空间。
FontCreator可以从ttc文件提取单个ttf文件。然后丢给fonttools处理。
核心的流程是：
- 导入ttf字体
- 生成新的映射name
- 生成映射空间：U+E000-F8FF
- 保存映射表

具体实现在这篇文章上做了修改：[使用 fonttools 自定义字体实现 WebFont 反爬虫](https://seealso.cn/web/use-fonttools-build-webfont-to-anti-crawler)。
得到的字符映射表不能暴露，否则就白干了
```bash
zip -P <a_long_random_password> cmap.json
```
如果是winrar操作，记得勾选“zip传统加密”
{% asset_img zip传统加密.png zip传统加密 %}
否则linux上解密报错
```
unsupported compression method 99
```
密码可以保存到travis ci。具体可以参照
- {% post_link travis-deploy-both-github-and-gitee %}


# hexo应用自定义字体

修改`themes\next\source\css\_custom\custom.styl`
```css
@font-face {
  font-family: myfont;
  src: url("/fonts/myfont.ttf");
  unicode-range: U+E000-F8FF;
}

p {
    font-family: myfont;
}
```
css的font-face可以描述自定义字体。
一开始在body上修改，发现不生效，索性直接改在p上。

# 替换markdown文件字符

有了自定义字体文件、字符映射表，就剩下怎么在html文件替换字符了。
替换markdown文件比替换生成的html要简单。
静态站点使用travis ci构建部署，因此可以放心操作markdown文件，不影响源码分支。
- 把字符映射表加密提交git
- 密码交给travis ci托管
- travis ci构建步骤，在hexo g之前，先解压缩字符映射表，再执行python脚本，替换所有的markdown文件。

剩下的细节点是替换脚本。一个典型的hexo markdown是
```yml
---
title: 反爬虫系列之2：字体反爬
date: 2019-08-31 18:09:59
tags: [爬虫]
categories: [爬虫]
keywords: [字体反爬, fonttools]
description:
---

# xxx

{% asset_img a.png %}

[]()
![]()

\`\`\`java
public static void main(String[] args) {

}
\`\`\`

```
如果无脑全局替换就会挖坑了。链接可能打不开，代码块也有问题（因为html生成为`<pre>`标签，里面的内容不做转义），甚至seo也很糟糕。
结论是meta信息、标题、代码块、超链接、图片链接等都不能替换。
因此脚本要识别当前行是否处于meta块、代码块之内，这一行是不是标题，是不是处于图片、超链接等。

# 参考

- [Recommendations for OpenType Fonts](https://docs.microsoft.com/en-us/typography/opentype/spec/recom)
