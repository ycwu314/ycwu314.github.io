---
title: chrome 80 SameSite 问题
date: 2020-03-18 19:40:50
tags: [浏览器, web]
categories: [web]
keywords: [chrome SameSite]
description: chrome 80 以后版本cookies默认增加SameSite=Lax配置，可能导致第三方cookies问题。
---

# 背景

浏览器升级到chrome 80，结果CAS登录无限跳转。
经同事指出，是因为chrome 80以后默认SameSite属性问题导致。
<!-- more -->

# cookies的SameSite属性

http协议是无状态的，于是有了通过附加cookies来存储状态信息。服务器响应增加`Set-Cookie`头部告诉浏览器在cookies保存信息。浏览器再次发送请求，则附加cookies字段。
```
Set-Cookie: is_login=1
```
但是，如果每个请求都附加cookies，又有新的问题：
- cookies消耗上传带宽。上行带宽本来就比较小，cookies最大可以去到4KB，每个请求都带上的话带宽非常可观。
- CSRF攻击可以获取cookies，导致安全隐患。

为了从源头减少CSRF攻击的危害，cookies增加了`SameSite`属性，控制向哪些站点发送cookies。

1. None
关闭SameSite属性。则允许发送cookies。前提是必须同时设置Secure属性（Cookie 只能通过 HTTPS 协议发送），否则无效。
```
Set-Cookie: is_login=1; SameSite=None; Secure
```

2. Lax
对于某些“安全”的方法，允许发送第三方cookies。比如：
- get方法。因为get的语义是“只读”
- 链接
- 预加载，`<link rel="prerender" href="..."/>`

如果向其他站点发送ajax请求、pos请求，则不会附加cookies。
```
Set-Cookie: is_login=1; SameSite=Lax;
```
**重点chrome 80以后Lax是默认值。**

3. Strict
跨站点无论如何都不发送第三方cookies。但是可能导致某些站点访问不正常。比如`a.taobao.com`和`s.taobao.com`被认为2个站点的话就不会正常识别登录状态（假设而已）
```
Set-Cookie: is_login=1; SameSite=Strict;
```


# 如何判断same-site还是cross-site

SameSite属性引发了一个问题，如何判断是同站点、跨站点？
通常根据二级域名区分。比如`ycwu314.top`和`www.ycwu314.top`是同站点。
但是，gitpage托管站点，例如`a.github.io`和`b.github.io`明显是属于不同的站点。
实际上，浏览器通常根据[public suffix list](https://publicsuffix.org/)区分站点。


# 修改chrome SameSite配置

在chrome中打开地址：
```
chrome://flags/#same-site-by-default-cookies
```

{% asset_img chrome-samesite-config.png chrome-samesite-config %}

# 参考

- [draft-ietf-httpbis-cookie-same-site-00](https://tools.ietf.org/html/draft-ietf-httpbis-cookie-same-site-00#section-4.1.1)