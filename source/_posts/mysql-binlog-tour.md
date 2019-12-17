---
title: mysql binlog 初体验
date: 2019-12-17 14:41:56
tags: [mysql, binlog]
categories: [mysql]
keywords: [mysql binlog, mysqlbinlog]
description: mysql binlog 基本操作。
---

业务上引入canal + binlog 解析作为mysql数据实时同步解决方案。于是整理下binlog相关运维资料。
<!-- more -->

# 开启binlog

修改my.cnf。
```
[mysqld]
server-id=1
log_bin=ON
log_bin_basename=/var/lib/mysql/mysql-bin
log_bin_index=/var/lib/mysql/mysql-bin.index
binlog_format=row
```

最小配置只需要`server-id`和`log_bin`：
```
[mysqld]
server-id=1
log_bin=/var/lib/mysql/mysql-bin.log
binlog_format=row
```
因为使用了canal同步，因此`binlog_format=row`。

然后重启mysqld。

检查是否开启binlog：
```
mysql> show variables like 'log_bin%';
+---------------------------------+--------------------------------+
| Variable_name                   | Value                          |
+---------------------------------+--------------------------------+
| log_bin                         | ON                             |
| log_bin_basename                | /var/log/mysql/mysql-bin       |
| log_bin_index                   | /var/log/mysql/mysql-bin.index |
| log_bin_trust_function_creators | OFF                            |
| log_bin_use_v1_row_events       | OFF                            |
+---------------------------------+--------------------------------+
5 rows in set
```
`log_bin`是`ON`则开启binlog成功。


# binlog操作

## 查看所有binlog

```
mysql> show master logs;
+------------------+-----------+
| Log_name         | File_size |
+------------------+-----------+
| mysql-bin.000001 | 164416086 |
| mysql-bin.000002 |   9257415 |
| mysql-bin.000003 |   3240423 |
+------------------+-----------+
3 rows in set
```

## 查看正在使用的binlog

```
mysql> show master status;
+------------------+----------+--------------+------------------+-------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
+------------------+----------+--------------+------------------+-------------------+
| mysql-bin.000003 |  3265489 |              |                  |                   |
+------------------+----------+--------------+------------------+-------------------+
1 row in set
```
position是当前的记录位置。


## 刷新binlog文件

新建一个binlog文件。
```
mysql> flush logs;
Query OK, 0 rows affected

mysql> show master status;
+------------------+----------+--------------+------------------+-------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
+------------------+----------+--------------+------------------+-------------------+
| mysql-bin.000004 |     1633 |              |                  |                   |
+------------------+----------+--------------+------------------+-------------------+
1 row in set
```
可以用来保留现场。

## 清空binlog

删除所有binlog文件，binlog序号复位，从0开始。
```
mysql> reset master;
Query OK, 0 rows affected

mysql> show master status;
+------------------+----------+--------------+------------------+-------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
+------------------+----------+--------------+------------------+-------------------+
| mysql-bin.000001 |     1074 |              |                  |                   |
+------------------+----------+--------------+------------------+-------------------+
1 row in set
```

**高能警告：**
不要删除正在使用的binlog文件，会导致同步工具异常。参见这个文章：
- {% post_link canal-in-practise-env %}


# 查看 binlog

## mysql client

很简单
```
mysql> show binlog events [IN 'log_name'] [FROM pos] [LIMIT [offset,] row_count];
```

## mysqlbinlog

mysqlbinlog使用要小心
```
--start-datetime 开始时间
--stop-datetime  结束时间
--database=resource 选择数据库
--result-file 结果输出到某个文件
--base64-output=decode-rows 
--start-position 开始位置
--stop-position 结束位置
```
完整参数见`--help`。

```
--base64-output=name 
                    Determine when the output statements should be
                    base64-encoded BINLOG statements: 'never' disables it and
                    works only for binlogs without row-based events;
                    'decode-rows' decodes row events into commented
                    pseudo-SQL statements if the --verbose option is also
                    given; 'auto' prints base64 only when necessary (i.e.,
                    for row-based events and format description events).  If
                    no --base64-output[=name] option is given at all, the
                    default is 'auto'.                
```


一个例子：
```
mysqlbinlog --no-defaults --database=xxx --start-position=377 --stop-position=583 --base64-output=decode-row mysql-bin.000001
```
效果如下：
```
/*!50530 SET @@SESSION.PSEUDO_SLAVE_MODE=1*/;
/*!50003 SET @OLD_COMPLETION_TYPE=@@COMPLETION_TYPE,COMPLETION_TYPE=0*/;
DELIMITER /*!*/;
# at 377
#191217 14:59:26 server id 1  end_log_pos 583 CRC32 0x0092f046  Update_rows: table id 155 flags: STMT_END_F
SET @@SESSION.GTID_NEXT= 'AUTOMATIC' /* added by mysqlbinlog */ /*!*/;
DELIMITER ;
# End of log file
/*!50003 SET COMPLETION_TYPE=@OLD_COMPLETION_TYPE*/;
/*!50530 SET @@SESSION.PSEUDO_SLAVE_MODE=0*/;
```

# unknown variable 'default-character-set=utf8'

最初使用mysqlbinlog读取binlog，遇到问题：
```
$ mysqlbinlog mysql-bin.000001
mysqlbinlog: unknown variable 'default-character-set=utf8'
```
原因是mysqlbinlog无法识别binlog中的配置中的default-character-set=utf8这个配置。解决方式有2个：

1. 修改my.cnf，然后重启mysqld
```ini
[mysql]
default-character-set = utf8
[mysqld]
character_set_server = utf8
```

2. 或者，使用`--no-defaults`选项
```
mysqlbinlog --no-defaults mysql-bin.000001
```


# 从 binlog 恢复

```
mysqlbinlog <binlog file> | mysql -u用户名 -p密码 数据库名
```
先找到要恢复的开始/结束时间，或者position范围。
然后把对应的binlog重放一次。
参考资料的链接有案例。

mysqlbinlog恢复要避免无穷复制问题：数据库A读取自己的binlog，然后写回数据库A。因为恢复的时候也会产生binlog，导致无限循环。
解决的办法是恢复阶段禁用binlog，涉及选项如下：
```
-D, --disable-log-bin 
                    Disable binary log. This is useful, if you enabled
                    --to-last-log and are sending the output to the same
                    MySQL server. This way you could avoid an endless loop.
                    You would also like to use it when restoring after a
                    crash to avoid duplication of the statements you already
                    have. NOTE: you will need a SUPER privilege to use this
                    option.

-t, --to-last-log   Requires -R. Will not stop at the end of the requested
                    binlog but rather continue printing until the end of the
                    last binlog of the MySQL server. If you send the output
                    to the same MySQL server, that may lead to an endless
                    loop.                        
```

# 清理 binlog

1. 删除所有binlog： `reset master;` 。
2. 开启一个新的binlog，不影响已有文件：`flush logs;` 。 
3. 配置自动删除，修改my.cnf并且重启：

```
[mysqld]
expire_logs_days = x  //二进制日志自动删除的天数。默认值为0,表示“没有自动删除”
```

4. 手动清理日志

```
purge master logs to 'mysql-bin.000005';           //指定清理某文件前所有的文件
purge master logs before '2019-12-15 00:00:00';        
purge master logs before  date_sub( now( ), interval 7 day);  
```

温馨提示：
不要删除正在使用的binlog文件，会导致同步工具异常。
不要删除正在使用的binlog文件，会导致同步工具异常。
不要删除正在使用的binlog文件，会导致同步工具异常。

# 参考

- [MySQL的binlog日志](https://www.cnblogs.com/martinzhang/p/3454358.html)


