---
title: cas实战笔记
date: 2020-09-09 16:10:50
tags: [CAS]
categories: [CAS]
keywords: []
description:
---

CAS使用和问题排查整理。
<!-- more -->

# 传统filter接入

引入依赖
```xml
<dependency>
    <groupId>org.jasig.cas.client</groupId>
    <artifactId>cas-client-core</artifactId>
    <version>3.5.0</version>
</dependency>
```

在web.xml中添加Cas Client 的拦截过滤配置：
```xml
<!-- 用于单点退出的fiflter -->
<filter>
    
    <filter-name>CAS Single Sign Out Filter</filter-name>
    <filter-class>org.jasig.cas.client.session.SingleSignOutFilter</filter-class>
    <init-param>
        <param-name>casServerUrlPrefix</param-name>
        <param-value>http://cas-server.com:8080/cas</param-value>
    </init-param>
</filter>
 
<listener>
    <listener-class>org.jasig.cas.client.session.SingleSignOutHttpSessionListener</listener-class>
</listener>

<!--注意casServerLoginUrl指cas server服务器的login地址；而serverName指的是应用的地址 --> 
<filter>
    <filter-name>CAS Authentication Filter</filter-name>
    <filter-class>org.jasig.cas.client.authentication.AuthenticationFilter</filter-class>
    <init-param>
        <param-name>casServerLoginUrl</param-name>
        <param-value>http://cas-server.com:8080/cas/login</param-value>
    </init-param>
    <init-param>
        <param-name>serverName</param-name>
        <param-value>http://client.app.com:8070</param-value>
    </init-param>
</filter>


<!-- 这个是对st票据的校验，其实cas中也就是通过这种方式来确定是否是同一个人 -->
<filter>
    <filter-name>CAS Validation Filter</filter-name>
    <filter-class>org.jasig.cas.client.validation.Cas20ProxyReceivingTicketValidationFilter</filter-class>
    <init-param>
        <param-name>casServerUrlPrefix</param-name>
        <param-value>http://cas-server.com:8080/cas</param-value>
    </init-param>
    <init-param>
        <param-name>serverName</param-name>
        <param-value>http://client.app.com:8070</param-value>
        </init-param>
</filter>
 
<filter>
    <filter-name>CAS HttpServletRequest Wrapper Filter</filter-name>
    <filter-class>org.jasig.cas.client.util.HttpServletRequestWrapperFilter</filter-class>
</filter>
 
<filter-mapping>
    <filter-name>CAS Single Sign Out Filter</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
 
<filter-mapping>
    <filter-name>CAS Validation Filter</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
 
<filter-mapping>
    <filter-name>CAS Authentication Filter</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
 
<filter-mapping>
    <filter-name>CAS HttpServletRequest Wrapper Filter</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
```

1. 这里没有spring security，没有shiro。
2. 如果有shiro，那么cas filter要配置在shiro之前。参见：[Shiro与CAS整合实现单点登录](https://www.cnblogs.com/funyoung/p/9242220.html)。


# No principal was found in the response from the CAS server


```
org.jasig.cas.client.validation.TicketValidationException: No principal was found in the response from the CAS server.
at org.jasig.cas.client.validation.Cas20ServiceTicketValidator.parseResponseFromServer(Cas20ServiceTicketValidator.java:82)
at org.jasig.cas.client.validation.AbstractUrlBasedTicketValidator.validate(AbstractUrlBasedTicketValidator.java:197)
at org.jasig.cas.client.validation.AbstractTicketValidationFilter.doFilter(AbstractTicketValidationFilter.java:164)
```


检查Cas20ProxyReceivingTicketValidationFilter配置casServerUrlPrefix服务地址。


# 票根'xxx'不符合目标服务

```
org.jasig.cas.client.validation.TicketValidationException: 
            票根'ST-1435-VDIliRQLn5rSsJw7Ldzc-cas01.example.org'不符合目标服务
    
	at org.jasig.cas.client.validation.Cas20ServiceTicketValidator.parseResponseFromServer(Cas20ServiceTicketValidator.java:84)
	at org.jasig.cas.client.validation.AbstractUrlBasedTicketValidator.validate(AbstractUrlBasedTicketValidator.java:201)
	at org.jasig.cas.client.validation.AbstractTicketValidationFilter.doFilter(AbstractTicketValidationFilter.java:204)
	at org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:193)
```

cas server已经生成了service ticket，当客户端拿着这张ST去服务端校验的时候出了问题。

常见的原因：
- AuthenticationFilter配置的serverName和Cas20ProxyReceivingTicketValidationFilter配置的serverName不一致。

这里是一个例子。用postman调用cas server restful接口获取tgt、获取st、使用st。
1. 获取tgt，使用的service是http://xxx.xxx.xxx.xxx:8088
2. 使用st，使用的service却是http://xxx.xxx.xxx.xxx:8088/dmserver/api/dataexplore/pca

cas server日志如下：
```
2020-09-09 13:47:41,611 INFO [org.jasig.inspektr.audit.support.Slf4jLoggingAuditTrailManager] - Audit trail record BEGIN
=============================================================
WHO: admin
WHAT: ST-1540-dEoj7dd4z0VWke2K47s4-cas01.example.org for http://xxx.xxx.xxx.xxx:8088
ACTION: SERVICE_TICKET_CREATED
APPLICATION: CAS
WHEN: Wed Sep 09 13:47:41 GMT+08:00 2020
CLIENT IP ADDRESS: 172.23.122.86
SERVER IP ADDRESS: 172.25.21.205
=============================================================


2020-09-09 13:47:48,855 INFO [org.jasig.cas.support.rest.TicketsResource] - 调用查询IP地址的接口
2020-09-09 13:48:04,200 ERROR [org.jasig.cas.CentralAuthenticationServiceImpl] - Service ticket [ST-1540-dEoj7dd4z0VWke2K47s4-cas01.example.org] with service [http://xxx.xxx.xxx.xxx:8088] does not match supplied service [http://xxx.xxx.xxx.xxx:8088/dmserver/api/dataexplore/pca]
2020-09-09 13:48:04,201 INFO [org.jasig.inspektr.audit.support.Slf4jLoggingAuditTrailManager] - Audit trail record BEGIN
=============================================================
WHO: audit:unknown
WHAT: ST-1540-dEoj7dd4z0VWke2K47s4-cas01.example.org
ACTION: SERVICE_TICKET_VALIDATE_FAILED
APPLICATION: CAS
WHEN: Wed Sep 09 13:48:04 GMT+08:00 2020
CLIENT IP ADDRESS: xxx.xxx.xxx.xxx
SERVER IP ADDRESS: 172.25.21.205
=============================================================
```


# 未能够识别出目标 'xxx'票根

```
javax.servlet.ServletException: org.jasig.cas.client.validation.TicketValidationException: 
            未能够识别出目标 'ST-1291-vzevZgDVjhN77R0PNP0s-cas01.example.org'票根
    
	org.jasig.cas.client.validation.AbstractTicketValidationFilter.doFilter(AbstractTicketValidationFilter.java:227)
	org.jasig.cas.client.session.SingleSignOutFilter.doFilter(SingleSignOutFilter.java:92)
	org.springframework.orm.jpa.support.OpenEntityManagerInViewFilter.doFilterInternal(OpenEntityManagerInViewFilter.java:178)
	org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:107)
```

常见原因：
1. 客户端带着ST去服务器验证，但此时服务器端的ST已经失效。默认ST有效期是10秒。
需要修改cas server。参见`cas.properties`：
```ini
##
# Service Ticket Timeout
# Default sourced from WEB-INF/spring-configuration/ticketExpirationPolices.xml
#
# Service Ticket timeout - typically kept short as a control against replay attacks, default is 10s.  You'll want to
# increase this timeout if you are manually testing service ticket creation/validation via tamperdata or similar tools
# st.timeToKillInSeconds=10
```

2. ST已经验签过。

# cas server restful api

cas server引入rest组件
```xml
<dependency>
    <groupId>org.apereo.cas</groupId>
    <artifactId>cas-server-support-rest</artifactId>
    <version>${cas.version}</version>
</dependency>
```

1. 获取TGT
```
POST /cas/v1/tickets HTTP/1.0
username=xxx&password=123456
```
请求响应
```
201 Created
Location: http://cas-server.com/cas/v1/tickets/{TGT id}
```

2. 获取ST
```
POST /cas/v1/tickets/{TGT id} HTTP/1.0
service={form encoded parameter for the service url}
```
请求响应
```
200 OK
ST-1572-kZsaCRRRFQGaKNmOw4Gr-cas01.example.org
```

3. 校验ST
```
GET /cas/p3/serviceValidate?service={service url}&ticket={service ticket}
```
请求响应200，可能是成功，也可能是失败。

4. 登出
```
DELETE /cas/v1/tickets/{TGT} HTTP/1.0
```
请求响应：返回注销的TGT

5. 使用ST
访问受保护的资源加上`?ticket={service ticket}`。


# 单点登出不成功

单点登出不成功，常见原因有：
1. 没有正确配置SingleSignOutFilter
2. service地址为localhost或者127.0.0.1，导致cas server不能正常通知client下线。


