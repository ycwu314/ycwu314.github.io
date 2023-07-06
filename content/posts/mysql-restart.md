---
title: 重启mysql服务
date: 2019-11-14 19:58:55
tags: [mysql]
categories: [mysql]
keywords: [mysql restart, systemctl service, skip-grant-tables]
description: 留意mysql系统服务的方式。skip-grant-tables选项会跳过权限表扫描，不要随便使用。
---

# 重启mysql

因为要做个canal binlog解析的demo，因此创建了canal账号。本地测试登录发现失败：
<!-- more -->
```
$ mysql -ucanal -p
Enter password: 
ERROR 1045 (28000): Access denied for user 'canal'@'localhost' (using password: YES)
```
密码是对的。
换成`-h 127.0.0.1`不行。
确认user表配置host是`%`。
感觉是mysql的问题，以前也遇到过，最后重启解决。

原本打算直接运行mysqld重启：
```
ubuntu@VM-0-2-ubuntu:/etc/mysql/mysql.conf.d$ mysqld
mysqld: Can't change dir to '/var/lib/mysql/' (Errcode: 13 - Permission denied)
2019-11-14T08:04:48.676534Z 0 [Warning] TIMESTAMP with implicit DEFAULT value is deprecated. Please use --explicit_defaults_for_timestamp server option (see documentation for more details).
2019-11-14T08:04:48.676649Z 0 [Warning] Can't create test file /var/lib/mysql/VM-0-2-ubuntu.lower-test
2019-11-14T08:04:48.676683Z 0 [Note] mysqld (mysqld 5.7.27-0ubuntu0.18.04.1) starting as process 644 ...
2019-11-14T08:04:48.684530Z 0 [Warning] Can't create test file /var/lib/mysql/VM-0-2-ubuntu.lower-test
2019-11-14T08:04:48.684554Z 0 [Warning] Can't create test file /var/lib/mysql/VM-0-2-ubuntu.lower-test
2019-11-14T08:04:48.684906Z 0 [Warning] One can only use the --user switch if running as root

2019-11-14T08:04:48.684943Z 0 [ERROR] failed to set datadir to /var/lib/mysql/
2019-11-14T08:04:48.684957Z 0 [ERROR] Aborting

2019-11-14T08:04:48.684970Z 0 [Note] Binlog end
2019-11-14T08:04:48.685016Z 0 [Note] mysqld: Shutdown complete
```

`One can only use the --user switch if running as root`，根据提示修改
```
ubuntu@VM-0-2-ubuntu:/etc/mysql/mysql.conf.d$ sudo mysqld --user mysql
ubuntu@VM-0-2-ubuntu:/etc/mysql/mysql.conf.d$ ps aux| grep mysqld
ubuntu     951  0.0  0.0  13772  1032 pts/3    S+   16:06   0:00 grep --color=auto mysqld
```
还是失败。尝试使用service
```
ubuntu@VM-0-2-ubuntu:/etc/mysql/mysql.conf.d$ sudo service mysqld restart
Failed to restart mysqld.service: Unit mysqld.service not found.
```
还是不成功。最后尝试systemctl
```
sudo systemctl start mysql.service
```
终于成功了。之后canal账号也能登录了。

小结：
- 留意安装mysql后建立的服务。这个mysql是使用apt安装，建立的服务方式是mysql.service。

# skip-grant-tables

对于之前的28000错误码，网上有的方法是使用`skip-grant-tables`选项。
具体是在`my.cnf`或者`/etc/mysql/mysql.conf.d/mysqld.cnf`增加
```
[mysqld]
skip-grant-tables
```
但是，**skip-grant-tables是在数据库启动的时候，跳跃权限表的限制，不用验证密码，直接登录**。
非常粗暴，非常危险。除非忘记root密码，否则不建议使用。

