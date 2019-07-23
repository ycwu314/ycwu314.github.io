---
title: 修复intellij打开properties文件乱码
date: 2019-07-23 18:27:12
tags: [技巧, java]
categories: [技巧]
keywords: [properties文件, 乱码, intellij]
description: Windows平台默认的字符编码是GBK，跨平台开发properties文件会产生乱码问题。
---

# 案例

项目之前是在windows上开发，没问题。今天朋友在mac上打开properties文件一堆乱码。。。又是编码问题。

在intellij配置里面搜索“encoding”，修改之前
{% asset_img idea_encoding.png %}
因为我的电脑是Windows，默认的系统编码就是GBK。GBK是微软的标准，在mac上打开当然有问题了。mac上的默认编码一般是utf8，具体使用`locale`命令可以查看。全部改成utf8即可。这样跨平台用utf8格式打开就不会乱码了。java应用也能正常访问。

**接下来要把原来的GBK文件转成utf8，因为配置只对新的文件生效！**
**接下来要把原来的GBK文件转成utf8，因为配置只对新的文件生效！**
**接下来要把原来的GBK文件转成utf8，因为配置只对新的文件生效！**
因为只有一个文件受影响，手动操作一下就好。用vscode以GBK编码打开原来的properties文件，确定中文不乱码，再复制到idea之中，保存即可。

但是会有另一个问题。原来的`老铁`，转码之后变成`\u8001\u94c1`。根本不是人看的。
idea有个相当窝心的选项，`Transparent native-to-ascii conversion`，打开之后会把properties文件的`\u8001\u94c1`又重新显示成中文。

最终效果如下。
{% asset_img idea_encoding_2.png %}

# 总结

编辑器的基础配置应该统一设置，避免产生类似问题。最近换了2台电脑，一时疏忽。
ps. 如果是正版的intellij，账号自带配置同步功能。。。家境贫寒，告辞。
