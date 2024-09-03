---
title: "HTTP3 Part 9：HTTP Alt-Svc Header"
date: 2024-09-03T14:48:46+08:00
tags: ["http3"]
categories: ["http3"]
description: Alt-Svc 帮助客户端平滑过渡到HTTP3服务。
---


在HTTP/3的上下文中，Alt-Svc头部对于连接的引导非常重要，因为HTTP/3需要QUIC传输协议，而客户端可能不直接支持QUIC，或需要连接到不同的端点。客户端可以连接到兼容HTTP/3的替代服务，从而可能提供更好的性能或可靠性。


# Alt-Svc


Alt-Svc 全称为“Alternative-Service”，直译为“备选服务”。该头部列举了当前站点备选的访问方式列表。一般用于在提供“QUIC”等新兴协议支持的同时，实现向下兼容。

在收到指示 HTTP/3 支持的有效标头后，浏览器将缓存此标头，并从那时起尝试设置 QUIC 连接。一些客户端会尽快执行此操作（即使在初始页面加载期间 - 见下文），而其他客户端会等到现有的 TCP 连接关闭。这意味着浏览器只有在首先通过 HTTP/2 或 HTTP/1.1 下载了至少一些资源后才会使用 HTTP/3。

```
语法
Alt-Svc: clear
Alt-Svc: <service-list>; ma=<max-age>
Alt-Svc: <service-list>; ma=<max-age>; persist=1

<max-age>可选
当前访问方式的有效期，超过该时间后，服务端将不保证该访问方式依旧可用，客户端应当重新获取更新后的 Alt-Svc 列表。单位为秒，默认值为 24 小时（86400)。

persist可选
可选参数，用于标识当前访问方式在网络环境改变时或者会话间始终保持。
```

Alt-Svc的另一个用途是负载均衡，可用于在不同的服务器或服务间分配负载，而不影响用户的请求路径。

# 对比 HTTP 重定向

HTTP 重定向，客户端会改变其请求的 URL，指向新的资源位置。

不同于使用 30x 状态码进行重定向分流，HTTP Alternative Services 只改变浏览器获取资源的网络方式，上层应用不会感觉到任何变化。



# 参考

- [HTTP Alternative Services 介绍](https://imququ.com/post/http-alt-svc.html)
- [HTTP/3：HTTP Alternative Services 作为协商方式](https://blog.skk.moe/post/http3-alt-svc/)

