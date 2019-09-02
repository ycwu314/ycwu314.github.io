---
title: postman自动计算md5加密验签
date: 2019-07-30 00:45:08
tags: [测试, 技巧]
categories: [测试]
keywords: [postman, md5加密, CryptoJS, 自动化测试]
description: postman可以发送请求的时候自动计算md5加密验签。原理是利用CryptoJS计算md5，验签字段需要设置为postman的环境变量。
---

接口加了加密验签逻辑，具体是md5(salt+时间戳)。被某君吐槽说测试不方便啊能不能先关掉。其实没有必要打开又关闭验签功能，postman的pre-request script功能完全可以模拟客户端加密过程。
<!-- more -->
# 创建环境变量

接口使用了`tm`、`sign`字段，先创建环境变量
{% asset_img manage_env.png "postman environment" %}

# pre-request script脚本

```javascript
var tm = new Date().getTime()
var salt = 'F5ZeNjdP2IpoLYc3'
var sign = CryptoJS.MD5(salt + tm).toString()
postman.setEnvironmentVariable('tm', tm);
postman.setEnvironmentVariable('sign', sign);
```
使用CryptoJS计算md5加密。然后把`tm`、`sign`设置为环境变量。注意url参数的写法，是用双花括号包住环境变量：`tm={{tm}}`

{% asset_img pre_request_script.png "postman pre request script" %}

# 验证

点击`Send`、`Code`，可以看到tm和sign已经被替换了。
```
GET /test/hello2?tm=1564422732095&amp; sign=69b5e46368f3e1f3aa3be03ddd4b7dae HTTP/1.1
Host: localhost:8000
cache-control: no-cache
Postman-Token: f8388dfc-c1d7-4c99-a5f5-5839f31da081
```

so easy！