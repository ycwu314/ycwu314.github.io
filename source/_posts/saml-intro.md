---
title: saml简介
date: 2020-09-22 10:44:27
tags: [saml]
categories: [saml]
keywords: 
description:
---


CAS SSO使用了SAML协议，做下笔记。
<!-- more -->

# what is

安全断言标记语言（英语：Security Assertion Markup Language，简称SAML）。SAML是OASIS安全服务技术委员会的一个产品。它在当事方之间交换身份验证和授权数据，尤其是在身份提供者和服务提供者之间交换。

了解SAML可以看官方的技术规范：
- [Security Assertion Markup Language (SAML) 2.0 Technical Overview](https://www.oasis-open.org/committees/download.php/11511/sstc-saml-tech-overview-2.0-draft-03.pdf)

# saml角色和流程

saml三个核心角色：
- SP（service provider），服务提供者
- IDP（identity provider），认证用户并生成断言
- client，用户。

三者的典型交互流程如下：
{% asset_img Saml-Authentication-Final.webp %}

# saml组件和报文

{% asset_img saml-components.png %}

saml最核心组件是assertion：
>XML-formatted tokens that are used to transfer user identity information, such as the authentication, attribute, and entitlement information, in the messages.

请求报文和响应报文demo如下。
{% asset_img saml-authn-request.png %}
请求主要包含谁来请求验证。

{% asset_img saml-authn-response.png %}
响应主要包含是否验证成功。

因为SAML是基于XML的（通常比较长），完整认证请求消息/响应消息要经过压缩（为Url节省空间）和编码（防止特殊字符）才能传输。

# saml使用场景

官方提供了2类使用场景：
- SSO
- 联合身份认证。Federation

## SSO

>As CarRentalInc.com trusts AirlineInc.com it knows that the user is valid 
>and creates a session for the user based on the user's name and/or the user attributes. 

{% asset_img saml-sso.png %}

## Federation

Federation是指一个用户在不同service provider以不同的用户名注册，然后以某种方式，把这个两个账号指向同一个人。

>This use case illustrates the “account linking” facet of federation. 
>The same user is registered on both sites, however using different names. 
>On CarRentalInc.com he is registered as jdoe and on HotelBookings.com as johnd.
>Account Linking enables a pseudonym to be established that links the two accounts

{% asset_img saml-federation.png %}

# saml和云服务的实践

云服务可以提供基于 SAML 2.0 联合身份验证，实现企业内部账号和云服务提供商的互通。
以腾讯云为例
{% asset_img tencent-cloud-1.png %}

{% asset_img tencent-cloud-2.png %}

留意IDP应该和具体的用户账号数据分离（比如LDAP、database等）。

具体参照：[基于 SAML 2.0 联合身份验证](https://cloud.tencent.com/document/product/598/30286)