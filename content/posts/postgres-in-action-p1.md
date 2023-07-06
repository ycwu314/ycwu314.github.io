---
title: postgres实战：日常问题记录
date: 2020-07-31 17:37:28
tags: [postgres]
categories: [postgres]
keywords: [postgres ident, postgres template busy]
description:
---
postgres日常问题记录。
<!-- more -->

# 认证配置

kong 2.1.0整合postgres 12.2，报错
```
[postgres error] could not retrieve current migrations: [postgres error]
Error: /usr/local/share/lua/5.1/kong/cmd/start.lua:28: [postgres error] could not retrieve current migrations: [postgres error] 致命错误: 用户 "kong" Ident 认证失败
```

postgres常见的四种身份验证为：
- trust：凡是连接到服务器的，都是可信任的。只需要提供psql用户名，可以没有对应的操作系统同名用户；
- password 和 md5：对于外部访问，需要提供 psql 用户名和密码。对于本地连接，提供 psql 用户名密码之外，还需要有操作系统访问权。（用操作系统同名用户验证）password 和 md5 的区别就是外部访问时传输的密码是否用 md5 加密；
- ident：对于外部访问，从 ident 服务器获得客户端操作系统用户名，然后把操作系统作为数据库用户名进行登录对于本地连接，实际上使用了peer；
- peer：通过客户端操作系统内核来获取当前系统登录的用户名，并作为psql用户名进行登录。

postgres的默认安全策略比较高，导致外部访问失败。

解决方法：
```
vi /var/lib/pgsql/12/data/pg_hba.conf
# 把这个配置文件中的认证 METHOD的ident修改为trust，可以实现用账户和密码来访问数据库，
```

# template数据库忙

创建kong数据库，遇到这样的问题：
>ERROR:  source database "template1" is being accessed by other users
>DETAIL:  There is 1 other session using the database.

`CREATE DATABASE`实际上通过拷贝一个已有数据库进行工作。默认情况下，它拷贝名为template1的标准系统数据库。如果你为template1数据库增加对象，这些对象将被拷贝到后续创建的用户数据库中。

系统里还有名为template0的第二个标准系统数据库。这个数据库包含和template1初始内容一样的数据，也就是说，只包含你的PostgreSQL版本预定义的标准对象。在数据库集簇被初始化之后，不应该对template0做任何修改。

从template0而不是template1复制的常见原因是， 可以在复制template0时指定新的编码和区域设置。

也可以指定使用的template
```sql
CREATE DATABASE dbname TEMPLATE template0;
```

当源数据库被拷贝时，不能有其他会话连接到它！
当源数据库被拷贝时，不能有其他会话连接到它！
当源数据库被拷贝时，不能有其他会话连接到它！

解决：
- 关闭多余的连接
- 重启pgsql
- 或者，使用其他数据库作为模板

扩展阅读：[模板数据库](http://www.postgres.cn/docs/12/manage-ag-templatedbs.html)