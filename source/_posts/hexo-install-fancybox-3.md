---
title: hexo fancybox 3安装问题
date: 2019-08-05 19:47:51
tags: [hexo]
categories: [技巧]
keywords: [hexo fancybox, .gitignore]
description: 在一个仓库里面git clone另一个仓库，会把对方的.gitignore文件下载并且生效。使用hexo g会忽略.gitignore涉及的文件。
---
上次在搞travis部署码云，途中遇到过一个奇怪的问题：使用traivs生成的静态页少了fancybox的库，页面加载失败。但是我本机hexo生成和部署就没有这个问题。

# 安装fancybox3

打开hexo next主题的`_config.yml`
```yml
# Fancybox. There is support for old version 2 and new version 3.
# Choose only one variant, do not need to install both.
# To install 2.x: https://github.com/theme-next/theme-next-fancybox
# To install 3.x: https://github.com/theme-next/theme-next-fancybox3
fancybox: true
```
然后参照fancy box 3.x版本的说明，git clone到next主体的lib目录，相对于项目路径是`themes\next\source\lib`。

# hexo next的.gitigonre文件

使用next主题，`source`目录下面的内容会拷贝到最终静态内容目录`public`（位于项目顶级目录）。
但是`hexo g`的日志输出是没有fancybox文件。可是文件明明就在这里，为什么没有拷贝到`public`呢？

只能是在某个地方被排除掉。hexo next主题的`_config.yml`和项目的`_config.yml`搜索fancybox，不是这个问题。
怀疑是某个隐藏文件做了排除，可能是gitignore文件。由于使用Windows，打开cmder一看，hexo next目录.gitignore文件有惊喜：
```
λ cat .gitignore
.DS_Store
.idea/
*.log
*.iml
yarn.lock
package-lock.json
node_modules/

# Ignore optional external libraries
source/lib/*

# Track internal libraries & Ignore unused verdors files
source/lib/font-awesome/less/
source/lib/font-awesome/scss/
!source/lib/font-awesome/*

!source/lib/jquery/

!source/lib/velocity/
```
回想起来，next主题是直接git clone到theme目录的方式安装的。.gitignore文件当然也被下载，并且生效。
其实以前也发生过一次fancybox文件部署之后找不到。不过当时直接拷贝一份到`public`目录，并没有认真想过这个问题。以后本地也没有`hexo clean`，所以拷贝到`public`的文件一直都在，没有重现过。
但是，出来混，迟早是要还的😂。

# 小结

使用git clone仓库安装插件，会连带下载.gitignore文件并且生效。可以考虑直接删除.gitignore文件。
