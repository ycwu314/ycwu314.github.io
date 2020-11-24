---
title: nginx gzip mime-type 配置
date: 2020-11-24 19:37:39
tags: [nginx, web]
categories: [nginx]
keywords:
description: nginx gzip要结合gzip_types配置才生效。
---

{% asset_img slug [title] %}

调试小程序接口，发现个别接口大小20+KB，有点奇怪。
一查发现是服务器没有正确配置压缩。
<!-- more -->

# http header和压缩

`accept-encoding`表示可以接收的编码类型（request header）。
`content-encoding`表示当前发送内容的编码类型（response header）。

请求header：
```
accept-encoding: gzip, deflate, br
```

响应header：
```
content-encoding: gzip
```

# nginx配置

`nginx.conf`配置了`gzip on`，但是没有`gzip_types`，默认只对`text/html`压缩。

```
Syntax:	gzip_types mime-type ...;
Default:	
gzip_types text/html;
Context:	http, server, location
Enables gzipping of responses for the specified MIME types in addition to “text/html”. The special value “*” matches any MIME type (0.8.29). Responses with the “text/html” type are always compressed.
```

于是增加：
```
gzip_types application/javascript text/css application/json application/xml text/xml text/plain
```

# springboot配置

也可以在springboot的application文件配置：
```ini
server.compression.enabled=true
server.compression.mime-types=application/javascript,text/css,application/json,application/xml,text/html,text/xml,text/plain
```

