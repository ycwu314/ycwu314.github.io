---
title: nginx配置SSL证书，以及ssl_ciphers选择
date: 2019-07-22 22:44:32
tags: [nginx, https, devops]
categories: [nginx]
keywords: [nginx配置ssl, ssl_ciphers, ssl_session_timeout, ssl_session_cache]
description: nginx配置ssl比较简单。nginx的ssl_ciphers决定服务器使用的加密套件，屏蔽不安全的加密套件能够提高安全性。ssllabs.com能够测试证书和服务器ssl配置安全性。ciphers的选择影响对旧系统、旧设备的兼容性。开启ssl_session_cache可以提高性能。
---

新域名备案一直等待回复，只能先使用旧域名和相应SSL证书。

# 准备

从SSL证书颁发者下载证书，不同的颁发者提供的证书和文件可能有出任，需要进行转换。通常包含key和pem两个文件。保存到服务器，并且确保nginx程序具有访问权限。
<!-- more -->
我把证书和密钥放在`/etc/nginx/cert`目录。

# ssllabs.com

`ssllabs.com`是一个很好的站点工具，检查证书安全、SSL配置安全、SSL已知漏洞检测。强烈安利。

# nginx配置

```nginx
server{
    listen 443 ssl;
    server_name "修改为您证书绑定的域名"; 
    ssl_certificate cert/cert.pem;          #将domain name.pem替换成您证书的文件名。
    ssl_certificate_key cert/cert.key;      #将domain name.key替换成您证书的密钥文件名。
    
    ssl_session_timeout 5m;
    ssl_session_cache shared:SSL:10m;
    
    ssl_prefer_server_ciphers on;         
    ssl_ciphers HIGH:!aNULL:!eNULL:!MD5:!RC4:!DES:!PSK:!EXPORT:!SHA:!SHA256;
    ssl_protocols TLSv1.2;   
}
```

## ssl_session_timeout, ssl_session_cache

ssl握手是一个消耗cpu资源的操作。因此在多个worker进程之间共享ssl session可以提升性能。
1M的缓存大概包含4000个session，默认的缓存超时时间为5分钟。考虑到小程序用完就走的场景，通常设置5min够用了。
**只用shared缓存要比built-in性能好**。参见[ssl_protocols](http://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_protocols)
>but using only shared cache without the built-in cache should be more efficient.

## ssl_prefer_server_ciphers

优先使用服务器端cipher配置。

## ssl_protocols

指定握手协议。
最新已经有TLS 1.3，但是需要openssl升级v1.1.1，以及客户端支持。以后再折腾。
TLS1.0、TLS1.1计划在2020年被废弃，直接忽略。
于是只保留TLS1.2。

## ssl_ciphers

ssl_ciphers配置使用的加密套件，使用OpenSSL的格式，具体可以参照[ciphers.html](https://www.openssl.org/docs/man1.1.0/man1/ciphers.html)

比如
>TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
代表的含义是：
>TLS - the protocol used
>ECDHE - the key exchange mechanism
>ECDSA - the algorithm of the authentication key
>AES - the symmetric encryption algorithm
>128 - the key size of the above
>GCM - the mode of the above
>SHA256 - the MAC used by the algorithm

经常见到`HIGH:!aNULL`之类的配置。`HIGH`是一个ciphers宏，代表一系列组合。`!`代表不使用该cipher。使用命令查看配置的ciphers。
```bash
openssl ciphers -V 'HIGH:!aNULL'
```

记住一点，NULL相关的都加上`!`就是了。

aNULL是没有认证阶段。
>The cipher suites offering no authentication. This is currently the anonymous DH algorithms and anonymous ECDH algorithms. These cipher suites are vulnerable to "man in the middle" attacks and so their use is discouraged. 

NULL、eNULL是根本不加密。
>The "NULL" ciphers that is those offering no encryption. Because these offer no encryption at all and are a security risk they are not enabled via either the DEFAULT or ALL cipher strings. 

使用`HIGH:!aNULL:!eNULL`就高枕无忧吗，不是的，下面是`ssllabs.com`的测试结果，TLS1.2页面
{% asset_img slug v1_ciphers.png ciphers %}

点击`Safari 10 / iOS 10`，发现一堆weak提示
{% asset_img slug v1_cbc_sha.png "cbc sha" %}

cipher安全性的一些经验
- CHACHA20是goolge几年前对移动设备的优化算法，速度比AES快，也省电，一度是google极力推荐的。但是自从ARMv7支持硬件AES加密之后，chacha20就比不上了。
- MD5，RC4，DES，SHA1等都是已知不安全的选项，容易被攻击。
- SHA256，SHA384要比SHA1安全。但是CBC模式的SHA是不安全。GCM模式的SHA是安全的。
- 苹果旧设备默认是CBC_SHA256，CBC_SHA384
- 减少非安全ciphers能够提高安全性，但是对老的系统、设备兼容性下降，甚至握手失败。

推荐一个mozilla的站点 [Security/Server Side TLS](https://wiki.mozilla.org/Security/Server_Side_TLS)，里面有官方推荐的tls ciphers组合。一般情况选择`Intermediate compatibility (recommended)`就可以了。

更新后的ciphers配置
```nginx
server {
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
}
```

ps. 如果想要“Cipher Strength”得分更高，就把128bit相关的加密套件都去掉。

{% asset_img slug v1_cipher兼容性.png "cipher comaptibility" %}
再次测试，发现对ios8.4、osx10.10、ie11兼容性不好。不过都是化石级的系统了，直接忽略。

至此，最基本的ssl证书已经配置能用。接下来再做优化。