---
title: 使用nginx stream模块做端口转发
date: 2019-07-27 22:10:41
tags: [nginx, ssh, linux, 技巧]
categories: [nginx]
keywords: [nginx unknown directive stream, 端口转发, nginx load_module, ngx_stream_module.so]
description: stream是nginx的动态模块，要先加载，否则提示nginx unknown directive stream。在nginx.conf头部增加load_module /usr/lib/nginx/modules/ngx_stream_module.so; 即可。
---

之前提到使用ssh隧道访问隔离的mysql。
- {% post_link access-mysql-by-ssh-tunnel %}

nginx也可以实现数据转发。常见的是http请求的转发（7层）。新版本的nginx加入了stream模块，可以做tcp转发（4层）。

# 检查nginx stream模块

nginx v1.9.0之后新增stream模块，但不是默认安装。
```
nginx -V
```
如果有`--with-stream`则表明有安装stream模块（此处有伏笔）。

# 配置nginx
```
stream {
    upstream rds {
        server rm-wz9p9rpee32z381re.mysql.rds.aliyuncs.com:3306;
    }
    server {
        listen 3307;
        proxy_pass rds;
        proxy_connect_timeout 1h;
        proxy_timeout 1h;
    }
}
```
这里使用3307端口映射RDS的3306端口。
和http模块配置类似。具体参照[ngx_stream_core_module.html](http://nginx.org/en/docs/stream/ngx_stream_core_module.html)。

# 测试nginx stream配置

`nginx -t`，发现报错
```bash
# nginx -t
nginx: [emerg] unknown directive "stream" in /etc/nginx/nginx.conf:13
nginx: configuration file /etc/nginx/nginx.conf test failed
```
`nginx unknown directive stream`？怎么不认识stream指令呢？`nginx -V`明明有stream模块
```
--with-stream=dynamic
```
参考了这篇文章[unknown-directive-stream-in-etc-nginx-nginx-conf86](https://serverfault.com/questions/858067/unknown-directive-stream-in-etc-nginx-nginx-conf86)。 

dynamic……nginx支持动态模块，需要先载入才能使用。解决方法是`nginx.conf`文件开头加上：
```
load_module /usr/lib/nginx/modules/ngx_stream_module.so;
```
然后
```
# nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

# nginx -s reload
```

# ECS本地测试连接rds mysql
```bash
# mysql -h localhost -P3307 -uroot
ERROR 2002 (HY000): Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock' (2)
```
`-P`是端口，`-p`才是密码。
这里要注意，`localhost`作为host的话，会直接访问unix socket，然而ECS本地没有开启mysqld服务，导致报错。正确的方式是使用`127.0.0.1`作为host。

```bash
# mysql -h 127.0.0.1 -P3307 -uroot -p
Enter password: 
```

# 更新ECS安全组

ECS安全组策略放开3307端口的访问，这样就可以让外网访问到（从安全角度，强烈不建议）。




