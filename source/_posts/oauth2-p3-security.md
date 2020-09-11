---
title: oauth2系列3：安全讨论
date: 2020-09-10 19:45:03
tags: [oauth2]
categories: [oauth2]
keywords: []
description:
---

oauth2协议的安全考虑。
<!-- more -->

# token类型

oauth2支持2种token_type：Bearer类型和MAC类型。

## bearer

Bearer Token (RFC 6750) 用于OAuth 2.0授权访问资源，任何Bearer持有者都可以无差别地用它来访问相关的资源，而无需证明持有加密key。

Bearer实现资源请求有三种方式：Authorization Header、Form-Encoded Body Parameter、URI Query Parameter，这三种方式优先级依次递减。

因为Bearer token能够直接使用，为了提高安全性，应该使用https协议，防止中间人嗅探、修改、重放。

使用Bearer token不需要对请求计算哈希。

## mac

mac token除了携带授权服务器下发的token，客户端还要携带时间戳，nonce，以及在客户端计算得到的mac值等信息，并通过这些额外的信息来保证传输的可靠性。
因此client每次请求都要计算哈希，并且server用相同参数检验哈希是否正确。

client通过添加id、ts、nonce、mac字段到Authorization请求首部以发起对用户资源的请求。

server收到请求后：
>重新计算mac值，并与客户端传递的值进行比较
>确保(timestam, nonce, token)三个维度之前没有被请求过，以防止重放攻击
>验证scope，以及token

参考资料：[draft-hammer-oauth-v2-mac-token-05](https://tools.ietf.org/html/draft-hammer-oauth-v2-mac-token-05)


# redirect_uri 和 code

oauth2的授权码模式、简化模式都使用了redirect_uri，回调到请求者的服务器。
授权码模式请求：
```
GET http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/auth?response_type=code&state=b85d54ce-8aba-4abf-8d35-79df50fdc3da&client_id=product-app&scope=openid&redirect_uri=https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fcallback HTTP/1.1
```

简化模式请求：
```
GET http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/auth?nonce=4c9bdcf0-37dc-47bc-82a4-36a877d4d462&response_type=token&state=b85d54ce-8aba-4abf-8d35-79df50fdc3da&client_id=product-app&scope=openid&redirect_uri=https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fcallback
```

攻击：
- 如果访问oauth2服务器不是使用https协议，那么攻击者很容易使用中间人攻击，篡改redirect_uri，指向恶意网站。

应对方案：
- oauth2访问优先使用https协议
- oauth2的实现就已经考虑到非https情况，在申请client的时候，指定合法的redirect_uri路径；并且在oauth2 server对redirect_uri进行校验。

ps. 一个小技巧。在外部oauth2服务提供商配置了外网域名作为redirect_uri，为了方便本地调试，修改本地hosts文件。

攻击：
- 记录code，然后重放获取access token

应对方案：
- oauth2 rfc就考虑到这个情况。code是一次性使用的。


# state

state参数可以为空，但是官方推荐传入。
在oauth2流程中，state参数回由oauth2 server在redirect_uri中原样返回。
开发者可以用这个参数验证请求有效性，也可以记录用户请求授权页前的位置。这个参数可用于防止跨站请求伪造（CSRF）攻击。

对oauth2登录实施CSRF攻击条件比较苛刻，可以参见：
- [小议OAuth 2.0的state参数](http://blog.sina.com.cn/s/blog_56b798f801018jyb.html)
