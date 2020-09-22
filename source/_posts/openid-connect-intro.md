---
title: OpenID Connect 简介
date: 2020-09-21 18:06:34
tags: [OpenID Connect]
categories: [OpenID Connect]
keywords: []
description:
---

# what is

OAuth2提供了Access Token来解决授权第三方客户端访问受保护资源的问题。
OpenID Connect(缩写为OIDC)在这个基础上提供了ID Token来解决第三方客户端标识用户身份认证的问题。

<!-- more -->

>OpenID Connect 1.0 is a simple identity layer on top of the OAuth 2.0 protocol. It allows Clients to verify the identity of the End-User based on the authentication performed by an Authorization Server, as well as to obtain basic profile information about the End-User in an interoperable and REST-like manner.

# 基本术语和流程

OpenID Connect有很多组件，最核心的是core。
{% asset_img OpenIDConnect-arch.png %}

OpenID Connect定义了几个术语：
- EU：End User：一个人类用户。
- RP：Relying Party ,用来代指OAuth2中的受信任的客户端，身份认证和授权信息的消费方；
- OP：OpenID Provider，有能力提供EU认证的服务（比如OAuth2中的授权服务），用来为RP提供EU的身份认证信息；
- ID Token：JWT格式的数据，包含EU身份认证的信息。
- UserInfo Endpoint：用户信息接口（受OAuth2保护），当RP使用Access Token访问时，返回授权用户的信息

OpenID Connect流程：
1. The RP (Client) sends a request to the OpenID Provider (OP).
2. The OP authenticates the End-User and obtains authorization.
3. The OP responds with an ID Token and usually an Access Token.
4. The RP can send a request with the Access Token to the UserInfo Endpoint.
5. The UserInfo Endpoint returns Claims about the End-User.

```
+--------+                                   +--------+
|        |                                   |        |
|        |---------(1) AuthN Request-------->|        |
|        |                                   |        |
|        |  +--------+                       |        |
|        |  |        |                       |        |
|        |  |  End-  |<--(2) AuthN & AuthZ-->|        |
|        |  |  User  |                       |        |
|   RP   |  |        |                       |   OP   |
|        |  +--------+                       |        |
|        |                                   |        |
|        |<--------(3) AuthN Response--------|        |
|        |                                   |        |
|        |---------(4) UserInfo Request----->|        |
|        |                                   |        |
|        |<--------(5) UserInfo Response-----|        |
|        |                                   |        |
+--------+                                   +--------+
```

其中AuthN=Authentication，表示认证；AuthZ=Authorization，代表授权。

OpenID Connect和Oauth 2的结合点在：
1. AuthN的时候，scope必须包含openid，这样就可以表明这是一个OIDC的请求。
2. AuthZ的返回，包含ID token。

结合一个例子来看就更清晰了：
{% asset_img jwt-openid-connect-sso-steps.png %}

ps：OIDC官方定义的一些scope：
{% asset_img OIDC-scope.png %}

# ID token

OpenID Connect在Oauth 2上的核心扩展是ID token，是一个授权服务器提供的包含用户信息（由一组Cliams构成以及其他辅助的Cliams）的JWT格式的数据结构。

ID Token的主要构成部分：
- iss = Issuer Identifier：必须。提供认证信息者的唯一标识。一般是一个https的url（不包含querystring和fragment部分）。
- sub = Subject Identifier：必须。iss提供的EU的标识，在iss范围内唯一。它会被RP用来标识唯一的用户。最长为255个ASCII个字符。
- aud = Audience(s)：必须。标识ID Token的受众。必须包含OAuth2的client_id。
- exp = Expiration time：必须。过期时间，超过此时间的ID Token会作废不再被验证通过。
- iat = Issued At Time：必须。JWT的构建的时间。
- auth_time = AuthenticationTime：EU完成认证的时间。如果RP发送AuthN请求的时候携带max_age的参数，则此Claim是必须的。
- nonce：RP发送请求的时候提供的随机字符串，用来减缓重放攻击，也可以来关联ID Token和RP本身的Session信息。
- acr = Authentication Context Class Reference：可选。表示一个认证上下文引用值，可以用来标识认证上下文类。
- amr = Authentication Methods References：可选。表示一组认证方法。
- azp = Authorized party：可选。结合aud使用。只有在被认证的一方和受众（aud）不一致时才使用此值，一般情况下很少使用。

OpenID Connect还定义了一堆官方的claims：[StandardClaims](https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims)。

**ID Token必须使用JWS进行签名和JWE加密。**

ID token是OpenID Connect的精髓所在：
- stateless session。因此后端服务可以更加灵活的扩容。
- 向第三方传递身份。这个id可以传递给第三方应用，或者后端服务，用于识别身份。
- token交换。ID token也可以用来交换access token。

# OpenID Connect验证流程

OIDC基于Oauth 2，支持3种认证方式：
- 授权码模式
- 简化模式
- 混合模式 hybrid

前两种和Oauth 2基本一致。这个就不展开了。
混合模式允许直接向客户端返回Access Token。因为直接返回，考虑到安全性，token有效时间尽量短。

在实现中，一个常见的改进是加入验证阶段promt字段。
以微软的OIDC实现为例：[Microsoft 标识平台和 OpenID Connect 协议](https://docs.microsoft.com/zh-cn/azure/active-directory/develop/v2-protocols-oidc)
>prompt表示需要的用户交互类型。 此时唯一有效值为 login、none 和 consent。 
>prompt=login 声明将强制用户在该请求上输入凭据，从而取消单一登录。 
>而 prompt=none 声明截然相反。 此声明确保用户不会看到任何交互式提示。 如果请求无法通过单一登录静默完成，Microsoft 标识平台终结点就会返回错误。 
>prompt=consent 声明会在用户登录后触发 OAuth 同意对话框。 该对话框要求用户向应用授予权限。


# OpenID Connect和SSO

之前研究了CAS的SSO，OpenID Connect也是可以做SSO的。
目前正处于draft状态。

## 单点登录

目前定义了针对移动设备的SSO流程：
```
+----------+     +----------+      +-----------+      +------------+
|  Native  |     |  Native  |      |  System   |      |            |
|  App     |     |  App     |      |  Browser  |      |    AS      |
|  #1      |     |  #2      |      |           |      |            |
+----+-----+     +----+-----+      +-----+-----+      +-----+------+
     |                |                  |                  |
     | [1] Start OIDC AuthN              |                  |
     +----------------+----------------> |                  |
     |                |                  | [2] /authorize   |
     |                |                  +----------------> |
     |                |                  |                  |
     |                |                  |   [3] authenticate
     |                |                  | <----------------|
     |                |                  |                  |
     |                |                  | [4] user creds   |
     |                |                  +----------------> |
     |                |                  |                  |
     |                |                  |  [5] callback    |
     |                |                  | <----------------+
     |  [6] callback with code           |                  |
     | <--------------+------------------+                  |
     |                |                  |                  |
     |  [7] exchange code for tokens     |                  |
     +----------------+-----------------------------------> |
     |                |                  |                  |
     |     [8] tokens (including device_secret)             |
     | <--------------+------------------+------------------+
     |                |                  |                  |
     |                |                  |                  |
     |                |                  |                  |
     +                +                  +                  +

```
这里新增了`device_secret`以及`device_sso`（图中没有标记）。

>In the context of this extension the device secret may be shared between mobile apps that can obtain the value via the shared security mechanism (e.g. keychain on iOS). If a mobile app requests a device secret via the device_sso scope and a device_secret exists, then the client MUST provide the device_secret on the request to the /token endpoint to exchange code for tokens. 


而当另一个app访问时，触发token交换和刷新
```
+----------+     +----------+      +-----------+      +------------+
|  Native  |     |  Native  |      |  System   |      |            |
|  App     |     |  App     |      |  Browser  |      |    AS      |
|  #1      |     |  #2      |      |           |      |            |
+----+-----+     +----+-----+      +-----+-----+      +-----+------+
     |                |                  |                  |
     |                |                  |                  |
     |                | [9] token exchange                  |
     |                +------------------+----------------> |
     |                |                  |                  |
     |                |                  |                  |
     |                |    [10] refresh, access, [device_secret]
     |                | <----------------+------------------|
     |                |                  |                  |
     |                |                  |                  |
     |                |                  |                  |
     +                +                  +                  +

```

其中定义了新的grant_type：`urn:ietf:params:oauth:grant-type:token-exchange`。
（Oauth 2协议的好处是可以利用grant_type来自定义流程）

参见：
- [OpenID Connect Native SSO for Mobile Apps 1.0 - draft 03](https://openid.net/specs/openid-connect-native-sso-1_0.html)

## 单点登出

和CAS类似，提供了front channel和back channel两种类型。
front方式依赖客户端向各个服务发送logout请求。
back方式由OIDC server负责向各个服务发送logout请求。back方式相比front更加可靠。

参见：
- [OpenID Connect Front-Channel Logout 1.0 - draft 04](https://openid.net/specs/openid-connect-frontchannel-1_0.html)
- [OpenID Connect Back-Channel Logout 1.0 - draft 06](https://openid.net/specs/openid-connect-backchannel-1_0.html)


# OpenID Connect 小结

- OAuth2提供了Access Token来解决授权第三方客户端访问受保护资源的问题
- OIDC在这个基础上提供了ID Token来解决第三方客户端标识用户身份认证的问题
- 基于Oauth 2的身份层
- 在Oauth 2请求中加入`scope=openid`
- Oauth 2授权响应增加ID token
- ID token是JWT，并且使用JWE或者JWS保护
- ID token包含了基本的用户信息，比如用户id
- OIDC可以扩展支持SSO

# 资料 

- [Welcome to OpenID Connect](https://openid.net/connect/)

