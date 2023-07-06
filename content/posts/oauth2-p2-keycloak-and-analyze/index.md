---
title: oauth2系列2：keycloak入门和4种模式抓包分析
date: 2020-09-09 20:09:31
tags: [oauth2]
categories: [oauth2]
keywords: []
description:
---

上一篇文章简单介绍了oauth2的4种模式。深入理解的最好方式抓包分析。
这里先准备oauth 2 authorization server，选择开源的keycloak。
然后介绍postman工具，方便发送oauth2请求。
最后对4种oauth2模式进行抓包分析。
<!-- more -->

# keycloak准备

去官网下载keycloak最新版本，解压缩之后使用`standalone.bat`运行单机版本。
默认的访问地址是`localhost:8080/auth`。
登录之后创建管理员账号。

接下来要创建realm、client、client scope、role、user。
具体参照这篇文章即可：[springboot整合keycloak](https://www.cnblogs.com/ifme/p/12591457.html)。

需要注意的是client配置。

1. client protocol：有openid connect和saml 两种，一般选择openid connnect。

2. access type: 如何触发登录流程。有3个选项：
- confidential：需要提供secret才能触发登录流程。
- public：不需要secret。
- bearer-only：不会触发登录流程，例如两个web service之间的通信。

3. 当access type为confidential，才会打开`Credential`选项页面。里面可以配置secret。
confidential类型可以开启全部4种oauth2模式。
public模式不支持client credential模式。

4. validate redirect urls：浏览器成功登录或者登出之后允许重定向的url。支持通配符，支持多个。
这里配置了postman的url，用于后续测试。

# springboot应用集成keycloak客户端

同样参照了这篇文章：[springboot整合keycloak](https://www.cnblogs.com/ifme/p/12591457.html)。

`application.properties`配置大概如下，其中被public-client折腾一下：
```ini
# keycloak auth服务器
keycloak.auth-server-url=http://localhost:8080/auth
keycloak.realm=SpringBoot
# clientID
keycloak.resource=product-app
keycloak.public-client=true
# if public client, then no need to set keycloak.credentials.secret
# keycloak.credentials.secret=81feaf6b-4544-4cc9-b05e-ae501f918a78

keycloak.securityConstraints[0].authRoles[0]=user
keycloak.securityConstraints[0].securityCollections[0].name= common user
keycloak.securityConstraints[0].securityCollections[0].patterns[0]=/products/*
```

realm里面client的access type：
- public：则配置`keycloak.public-client=true`（默认为false）
- confidential：则要配置`keycloak.credentials.secret`，内容为 keycloak -> clients -> Credential页面的secrect。

如果keycloak client配置为confidential，但是没有在客户端应用配置`keycloak.credentials.secret`，访问受保护资源就会提示报错：
```
2020-09-09 22:06:11.807  INFO 19256 --- [nio-8081-exec-1] o.keycloak.adapters.KeycloakDeployment   : Loaded URLs from http://localhost:8080/auth/realms/SpringBoot/.well-known/openid-configuration
2020-09-09 22:06:13.842  WARN 19256 --- [nio-8081-exec-2] a.a.ClientIdAndSecretCredentialsProvider : Client 'product-app' doesn't have secret available
2020-09-09 22:06:13.852 ERROR 19256 --- [nio-8081-exec-2] o.k.adapters.OAuthRequestAuthenticator   : failed to turn code into token
2020-09-09 22:06:13.852 ERROR 19256 --- [nio-8081-exec-2] o.k.adapters.OAuthRequestAuthenticator   : status from server: 400
2020-09-09 22:06:13.852 ERROR 19256 --- [nio-8081-exec-2] o.k.adapters.OAuthRequestAuthenticator   :    {"error":"unauthorized_client","error_description":"INVALID_CREDENTIALS: Invalid client credentials"}
```


# keycloak的rest端点

为了得到4种模式的抓包，先要知道keycloak的rest端口。

参照官方文档，一个realm提供的配置信息可以在这里查询
```
http://<keycloak server:port>/auth/realms/<realm>/.well-known/openid-configuration
```

```json
{
    "issuer": "http://localhost:8080/auth/realms/SpringBoot",
    "authorization_endpoint": "http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/auth",
    "token_endpoint": "http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/token",
    "introspection_endpoint": "http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/token/introspect",
    "userinfo_endpoint": "http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/userinfo",
    "end_session_endpoint": "http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/logout",
    "jwks_uri": "http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/certs",
    "check_session_iframe": "http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/login-status-iframe.html",
    "grant_types_supported": [
        "authorization_code",
        "implicit",
        "refresh_token",
        "password",
        "client_credentials"
    ],
    "response_types_supported": [
        "code",
        "none",
        "id_token",
        "token",
        "id_token token",
        "code id_token",
        "code token",
        "code id_token token"
    ],
    // 省略一堆
    "response_modes_supported": [
        "query",
        "fragment",
        "form_post"
    ],
    "registration_endpoint": "http://localhost:8080/auth/realms/SpringBoot/clients-registrations/openid-connect",
    "token_endpoint_auth_methods_supported": [
        "private_key_jwt",
        "client_secret_basic",
        "client_secret_post",
        "tls_client_auth",
        "client_secret_jwt"
    ],
    // 省略一堆
}
```

authorization_endpoint是授权入口。
token_endpoint是token入口，传入authorization code，兑换成access token。

# 使用postman操作oauth2流程

postman可以很方便的操作oauth2流程。



![postman-oauth2.png](postman-oauth2.png)





![postman-get-access-token.png](postman-get-access-token.png)



grant type可以选择不同模式。
其中authorization code和implicit模式需要提供callback url。
选择authorize using browser，则postman可以自动提取authorization code或者access token。
因此要在keycloak client配置中把postman回调地址加进去。

如果遇到问题，可以打开postman console查看请求和响应。
路径是View -> Show postman console。



![postman-console.png](postman-console.png)




# 授权码模式分析

>（A）用户访问客户端，后者将前者导向认证服务器。
>（B）用户选择是否给予客户端授权。
>（C）假设用户给予授权，认证服务器将用户导向客户端事先指定的"重定向URI"（redirection URI），同时附上一个授权码。
>（D）客户端收到授权码，附上早先的"重定向URI"，向认证服务器申请令牌。这一步是在客户端的后台的服务器上完成的，对用户不可见。
>（E）认证服务器核对了授权码和重定向URI，确认无误后，向客户端发送访问令牌（access token）和更新令牌（refresh token）。



![auth-code-1.png](auth-code-1.png)



1. 向认证服务器发送请求
```
GET http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/auth?response_type=code&state=b85d54ce-8aba-4abf-8d35-79df50fdc3da&client_id=product-app&scope=openid&redirect_uri=https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fcallback HTTP/1.1
```

query string参数:


![auth-code-2.png](auth-code-2.png)



字段说明：
- response_type：表示授权类型，必选项，此处的值固定为"code"
- client_id：表示客户端的ID，必选项
- redirect_uri：表示重定向URI，可选项
- scope：表示申请的权限范围，可选项
- state：表示客户端的当前状态，可以指定任意值，认证服务器会原封不动地返回这个值。


2. 认证服务器响应，要求重定向到请求时指定的redirect_uri
```
HTTP/1.1 302 Found
Location: https://oauth.pstmn.io/v1/callback?state=b85d54ce-8aba-4abf-8d35-79df50fdc3da&session_state=6ccd0eeb-3396-4af8-878e-98cc1de409c3&code=8a4a4295-bc4e-4ece-8dae-6b687ede60e3.6ccd0eeb-3396-4af8-878e-98cc1de409c3.7ec3571e-47d2-410f-997f-f9cc3c207ebe
```



![auth-code-3.png](auth-code-3.png)



字段说明：
- code：表示授权码，必选项。该码的有效期应该很短，通常设为10分钟，客户端只能使用该码一次，否则会被授权服务器拒绝。该码与客户端ID和重定向URI，是一一对应关系。
- state：如果客户端的请求中包含这个参数，认证服务器的回应也必须一模一样包含这个参数。

3. 用authorization code去交换access token
```
POST http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Authorization: Basic cHJvZHVjdC1hcHA6ODFmZWFmNmItNDU0NC00Y2M5LWIwNWUtYWU1MDFmOTE4YTc4

grant_type=authorization_code&code=8a4a4295-bc4e-4ece-8dae-6b687ede60e3.6ccd0eeb-3396-4af8-878e-98cc1de409c3.7ec3571e-47d2-410f-997f-f9cc3c207ebe&redirect_uri=https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fcallback&client_id=product-app
```



![auth-code-4.png](auth-code-4.png)



字段说明：
- grant_type：表示使用的授权模式，必选项，此处的值固定为"authorization_code"。
- code：表示上一步获得的授权码，必选项。
- redirect_uri：表示重定向URI，必选项，且必须与A步骤中的该参数值保持一致。
- client_id：表示客户端ID，必选项。

响应是一个json：


![auth-code-5.png](auth-code-5.png)



字段说明：
- access_token：表示访问令牌，必选项。
- token_type：表示令牌类型，该值大小写不敏感，必选项，可以是bearer类型或mac类型。
- expires_in：表示过期时间，单位为秒。如果省略该参数，必须其他方式设置过期时间。
- refresh_token：表示更新令牌，用来获取下一次的访问令牌，可选项。
- scope：表示权限范围，如果与客户端申请的范围一致，此项可省略。

# 简化模式

>简化模式（implicit grant type）不通过第三方应用程序的服务器，直接在浏览器中向认证服务器申请令牌，跳过了"授权码"这个步骤，因此得名。所有步骤在浏览器中完成，令牌对访问者是可见的，且客户端不需要认证。

简化模式又叫隐式模式。

**keyloak在简化模式需要提供nonce字段**，避免重放攻击，否则请求报错：
```
10:53:39,937 ERROR [org.keycloak.services] (default task-1) KC-SERVICES0092: Missing parameter: nonce
10:53:39,938 WARN  [org.keycloak.events] (default task-1) type=LOGIN_ERROR, realmId=spring, clientId=product-app, userId=null, ipAddress=127.0.0.1, error=invalid_request, response_type=token, redirect_uri=https://oauth.pstmn.io/v1/callback, response_mode=fragment
```

因此修改postman的auth url。guid是postman提供的guid风格的随机函数。
```
http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/auth?nonce={{$guid}}
```

1. 向认证服务器发送请求
```
GET http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/auth?nonce=4c9bdcf0-37dc-47bc-82a4-36a877d4d462&response_type=token&state=b85d54ce-8aba-4abf-8d35-79df50fdc3da&client_id=product-app&scope=openid&redirect_uri=https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fcallback
```



![implicit-1.png](implicit-1.png)




```
HTTP/1.1 302 Found
Location: https://oauth.pstmn.io/v1/callback#state=b85d54ce-8aba-4abf-8d35-79df50fdc3da&session_state=d518ff7b-0020-4e69-aee9-c7ea4f22f461&access_token=eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJKb2ZERWR2VWI4Uzk3VEV0bnM2LUQ3N1cxVzdGM0lnZHVhN1pLYmZxaWp3In0.eyJleHAiOjE1OTk3MDk0ODYsImlhdCI6MTU5OTcwODU4NiwiYXV0aF90aW1lIjoxNTk5NzA4MjQyLCJqdGkiOiI5YTNmMzBhNS00OWI1LTQ2ODQtOTc4My1iYjZhMmRjNGU3M2IiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwODAvYXV0aC9yZWFsbXMvU3ByaW5nQm9vdCIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiIwNzhkOTg4Yy0xMmI5LTRhZDgtYTA2YS1hZDExYWEzNTM3MzMiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJwcm9kdWN0LWFwcCIsIm5vbmNlIjoiNGM5YmRjZjAtMzdkYy00N2JjLTgyYTQtMzZhODc3ZDRkNDYyIiwic2Vzc2lvbl9zdGF0ZSI6ImQ1MThmZjdiLTAwMjAtNGU2OS1hZWU5LWM3ZWE0ZjIyZjQ2MSIsImFjciI6IjAiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsInVzZXIiXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJ0ZXN0dXNlciJ9.dTXMmVsdaHDuMH6oCyUpCIahZIYWdxYpv7txcU8ZMx90F8zJe17bTuamhZLyA_-X2iLfLaDtGrygHUBSitn5zyQq9luLQzxRKiyFrXDLg8YeH5jTBjgHdRiEp1aqChRKgsRs2la8sWyT1dnHeYuBXw5Exz0nA18EYFEI25j1QT40DSLPT9vc8OUfSbJQd9sxdLa_2J9GF5shWajQCeQJ45Ky-5RCCKbuwRidMCQHNWv1zhPFODOJpSW4T80-AmrtnHA-DDqorLsFrHOB8DuTjQo8SoCDBz9wq1Q0uT27ANqfs-Kt3CCFG2Y2NB70672tic45Bggt-Zi9gZ04NmLi3A&token_type=bearer&expires_in=900

```

响应直接返回了access_token。
从响应数据看，简化模式不能刷新token！


![implicit-2.png](implicit-2.png)


留意这里url使用了`#`（hash，`#fragment`部分），而非`?`。

下一步浏览器会访问Location指定的网址，但是Hash部分不会发送。接下来，服务提供商的资源服务器发送过来的代码，会提取出Hash中的令牌。

# 密码模式

>用户向客户端提供自己的用户名和密码。客户端使用这些信息，向"服务商提供商"索要授权。
>认证服务器只有在其他授权模式无法执行的情况下，才能考虑使用这种模式。

向认证服务器发送请求
```
POST http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Authorization: Basic cHJvZHVjdC1hcHA6ODFmZWFmNmItNDU0NC00Y2M5LWIwNWUtYWU1MDFmOTE4YTc4

grant_type=password&username=testuser&password=123456&scope=openid
```

请求头使用Authorization认证。
使用base64解密之后
```
product-app:81feaf6b-4544-4cc9-b05e-ae501f918a78
```
product-app是要访问的client id，后面是client secret。

字段说明：
- grant_type：表示授权类型，此处的值固定为"password"，必选项。
- username：表示用户名，必选项。
- password：表示用户的密码，必选项。
- scope：表示权限范围，可选项。

响应是json


![password-1.png](password-1.png)



# 客户端模式

>客户端模式（Client Credentials Grant）指客户端以自己的名义，而不是以用户的名义，向"服务提供商"进行认证。

请求
```
POST http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Authorization: Basic cHJvZHVjdC1hcHA6ODFmZWFmNmItNDU0NC00Y2M5LWIwNWUtYWU1MDFmOTE4YTc4

grant_type=client_credentials&scope=openid
```

请求头使用Authorization认证。

字段说明：
- grant_type：表示授权类型，此处的值固定为"clientcredentials"，必选项。
- scope：表示权限范围，可选项。

响应为json，不贴图了。

# 刷新token

>refresh token的初衷主要是为了用户体验不想用户重复输入账号密码来换取新token，因而设计了refresh token用于换取新token。

在refresh_token过期之前，都可以使用token端点获取新的access_token。

发送请求
```
POST http://localhost:8080/auth/realms/SpringBoot/protocol/openid-connect/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJkZmMzOTNjOS01NjhjLTQ4OGUtODgyNy1iMGI4YTcyMThjOGIifQ.eyJleHAiOjE1OTk3MjE0NDIsImlhdCI6MTU5OTcxOTY0MiwianRpIjoiYzhkZWU5ZGUtMjYyOC00ODUxLWEzZDAtNDQ4NWU2N2Y3ZTMwIiwiaXNzIjoiaHR0cDovL2xvY2FsaG9zdDo4MDgwL2F1dGgvcmVhbG1zL1NwcmluZ0Jvb3QiLCJhdWQiOiJodHRwOi8vbG9jYWxob3N0OjgwODAvYXV0aC9yZWFsbXMvU3ByaW5nQm9vdCIsInN1YiI6IjA3OGQ5ODhjLTEyYjktNGFkOC1hMDZhLWFkMTFhYTM1MzczMyIsInR5cCI6IlJlZnJlc2giLCJhenAiOiJwcm9kdWN0LWFwcCIsIm5vbmNlIjoiN2NlNmMzNzAtMzdhOC00YjE1LWEyYTAtMThlYzc1ZmFmMjMzIiwic2Vzc2lvbl9zdGF0ZSI6IjFmMzk5NjQ2LWU5ZDMtNDM1OC1hNGM0LTFiNmQwMWVkYTY3MiIsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwifQ.xBJSxJEcGkTPRmKS5dKU7Ov8bPmuVoP5_ff4ISYhU5w&client_id=product-app&client_secret=81feaf6b-4544-4cc9-b05e-ae501f918a78
```



![refresh-token.png](refresh-token.png)



响应为json。

# 四种授权模式的对比



![OAuth-Flow-Comparison.png](OAuth-Flow-Comparison.png)


图片来源： `https://blog.oauth.io/introduction-oauth2-flow-diagrams/`

1. 授权码模式
先获取code，再用code去换access token。
安全性高。
市面上大多数第三方app都使用。
支持refresh_token。

2. 简化模式
不需要后端服务，直接在前端获取token。
没有code，在redirect_uri直接返回token。
因为直接返回token，所以安全性变低，token的生命周期要尽量短。
比如单页应用。
不支持refresh_token。

3. 密码模式
client可能保存了用户密码，安全性低。
适合遗留项目升级。
支持refresh_token。

4. 客户端凭证模式
不需要用户参与，适合纯属两个服务之间的互操作。
不支持refresh_token（没有必要）。