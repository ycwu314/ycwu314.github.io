---
title: 解除静态网站的关注公众号弹窗
date: 2020-04-09 16:00:18
tags: [javascript]
categories: [技巧]
keywords: [网页验证码]
description: 解除静态网站的关注公众号弹窗。
---

搜索资料，导航到某些网站，“阅读更多”提示要“关注公众号输入验证码”。
<!-- more -->
{% asset_img readmore-1.png readmore %}

{% asset_img readmore-2.png 验证码弹窗 %}
这种引流方式挺烦人的。关注后还不是要取消。

想了想，这些静态模板网站，不太可能做动态验证码。应该是静态验证码。
chrome中打开调试面板，关注XHR请求，随便输入一堆字符提交，提示验证码错误，且没有发送网络请求。

嗯，验证码基本就是在页面里面，或者引用的js里面。
打开element tab，找到弹窗，记下验证码文本框的id("unlockCode")。
{% asset_img unlock-code-1.png 弹窗组件id %}

在页面、引用的js中查找“unlockCode”，终于找到了。
{% asset_img unlock-code-2.png 弹窗组件js %}

输入验证码后，保存了cookie，避免再出现弹窗。

搞定！