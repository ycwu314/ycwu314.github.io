---
title: csrf攻击和防范
date: 2019-08-05 23:42:55
tags: [web, 网络安全, nginx]
categories: [web]
keywords: [csrf攻击, csrf token, nginx referer, ngx_http_referer_module]
description: csrf攻击（英语：Cross-site request forgery）利用的是网站对用户网页浏览器的信任，伪造用户请求到其他站点。解决方法是服务器检查请求的合法性。使用referer可以简单检查请求来源，但是referer字段容易被伪造。自定义csrf token更加有效，可以放在cookie、header或者form表单的hidden字段。
---
# csrf是什么

来自wiki
>跨站请求伪造（英语：Cross-site request forgery），也被称为 one-click attack 或者 session riding，通常缩写为 CSRF 或者 XSRF，是一种挟制用户在当前已登录的Web应用程序上执行非本意的操作的攻击方法。跟跨网站脚本（XSS）相比，XSS利用的是用户对指定网站的信任，CSRF利用的是网站对用户网页浏览器的信任。
>简单的身份验证只能保证请求发自某个用户的浏览器，却不能保证请求本身是用户自愿发出的。

# 一个例子

网上很多是银行转账的例子，这里再编一个新的。用户访问`www.example.com`，看到大抽奖，毫不犹豫就点击了
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>喜迎5G上市幸运大抽奖</title>
</head>
<body>
<form method="get" action="http://www.xx-ads.com/click.do">
    <input type="hidden" name="ad_id" value="xxx">
    <input type="hidden" name="from_id" value="yyy">
    <input type="button" onclick="submit()" value="点击赢大奖">
</form>
</body>
```
然后就给某个广告投放者创造了一次点击（当然广告平台有反作弊机制啦）。

# 解决

csrf根源问题在于，服务器对请求来源不加以区分，即无条件信任来自浏览器的请求。

## 验证referer字段

http协议定义了`referer`字段，用来表示当前请求的来源，具体是url地址。使用referer字段可以简单判断请求来源。但是，referer字段很容易伪造。

## 自定义csrf token字段

因为A站点的页面不能获取B站点的页面内容、cookies，因此可以在提交页面上增加token字段。

1. 生成表单的时候增加hidden字段，用来存放服务器生成的token。提交表单的时候一起提交
```html
<input type="hidden" name="csrf-token" value="5QhM72KX9zjHO03V">
```
2. cookies返回token，因为获取不到其他站点的cookie。
3. token放在自定义的header，比如`X-CSRF-TOKEN`。

**不管token是放在hidden、cookies还是自定义header，都要在提交的时候在服务器端验证token的有效性**。  

服务器端可以使用filter、切面等方式统一验证token。

## 用户端防范

关键站点（比如跟💴相关的）使用完之后及时退出。这样伪造请求发出去，通常会挂在被攻击站点的登录态校验。

# 实战

## nginx限制referer字段

nginx使用[ngx_http_referer_module](http://nginx.org/en/docs/http/ngx_http_referer_module.html)处理referer字段。
```
valid_referers none blocked server_names
               *.example.com example.* www.example.org/galleries/
               ~\.google\.;

if ($invalid_referer) {
    return 403;
}
```
根据`valid_referers`的结果，`$invalid_referer`返回0或者1。
valid_referers支持的方式有：
- none：referer字段为空
- blocked：正常的referer字段是`http://`或者`https://`开头。其他为非正常的referer，比如`Referer:xxx`。通常是伪造请求，或者被防火墙修改。
- server_names：指定的服务器，支持通配符。

ps. nginx referer更多是用于简单的防盗链。

## 使用spring security

默认是开启csrf。
```
@Override
protected void configure(HttpSecurity http) throws Exception {
    http
      .csrf().disable();
}
```
然后在form增加
```html
<input type="hidden" name="${_csrf.parameterName}" value="${_csrf.token}"/>
```
剩下的交给spring security框架。
注意这个是form表单。如果是ajax方式提交，要自己获取csrf token，并且提交。

