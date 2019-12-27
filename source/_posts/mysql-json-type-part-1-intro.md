---
title: mysql json 系列1：简介
date: 2019-12-26 19:53:19
tags: [mysql]
categories: [mysql]
keywords: [mysql json]
description: mysql 5.7.8 新增json类型。
---

# 简介

Mysql 5.7.8 以后版本增加了json类型，支持json object和json array。
由于是原生支持，提供了json语法检查、特殊dml函数、也支持字段索引。
<!-- more -->

# 基本操作

mysql 5.7 / 8.0 基本的json函数如下：
{% asset_img mysql-json-function.png mysql-json-function %}

注意，json_append()、json_merge()函数已经在5.7.x废弃了。


json object
```json
{"cnt": 111, "some_attr": "hello"}

函数 JSON_OBJECT(key1,val1,key2,val2...)
```

json array
```json
["abc", 10, null, true, false]

函数 JSON_ARRAY(val1,val2,val3...)
```

convert函数支持字符串转换为json类型：
```sql
select convert('{"name": "aaa", "type": 22, "lucky": 33}', json)
```

怎么知道json字段具体是object还是array？使用json_type()测试：
```sql
mysql>  select json_type(extra) from t_person where id = 1;
+------------------+
| json_type(extra) |
+------------------+
| OBJECT           |
+------------------+
1 row in set (0.03 sec)
```

# 读取json数据


访问json里面的字段。
- `->`操作符，返回值带双引号。
- `->>`操作符，返回值去掉双引号，要求mysql version 5.7.13+。
```sql
mysql> select extra->'$.name' from t_person where id = 1;
+------------------+
| extra-> '$.name' |
+------------------+
| "aaa"            |
+------------------+
1 row in set (0.02 sec)

mysql> select extra->> '$.name' from t_person where id = 1;
+-------------------+
| extra->> '$.name' |
+-------------------+
| aaa               |
+-------------------+
1 row in set (0.02 sec)
```

也可以使用json_extract()提取数据
```sql
mysql> select json_extract(extra, '$.name') from t_person where id = 1;
+-------------------------------+
| json_extract(extra, '$.name') |
+-------------------------------+
| "aaa"                         |
+-------------------------------+
1 row in set (0.02 sec)
```

默认情况下，json类型以压缩字符串形式显示，太丑了？使用json_pretty()美化输出格式
```sql
mysql>  select json_pretty(extra) from t_person where id = 1;
+---------------------------------------------+
| json_pretty(extra)                          |
+---------------------------------------------+
| {
  "name": "aaa",
  "type": 22,
  "lucky": 1
} |
+---------------------------------------------+
1 row in set (0.05 sec)
```

想知道json字段的长度？使用json_storage_size()
```sql
mysql>  select json_storage_size(extra) from t_person where id = 1;
+--------------------------+
| json_storage_size(extra) |
+--------------------------+
|                       43 |
+--------------------------+
1 row in set (0.04 sec)
```

# 查找json数据

```
JSON_SEARCH(json_doc, one_or_all, search_str[, escape_char[, path] ...])
```
查询包含指定字符串的paths，并作为一个json array返回。如果有参数为NUL或path不存在，则返回NULL。
one_or_all："one"表示查询到一个即返回；"all"表示查询所有。
search_str：要查询的字符串。 可以用LIKE里的'%'或‘_’匹配。

# 修改json数据

`JSON_INSERT(json_doc, path, val[, path, val] ...)`
在指定path下插入数据，如果path已存在，则忽略此val（不存在才插入）。

`JSON_REPLACE(json_doc, path, val[, path, val] ...)`
替换指定路径的数据，如果某个路径不存在则略过（存在才替换）。如果有参数为NULL，则返回NULL。

`JSON_SET(json_doc, path, val[, path, val] ...)`
设置指定路径的数据（不管是否存在）。如果有参数为NULL，则返回NULL。

# 索引

为了加快数据检索，可以为json内部的字段创建virtual column，再建立索引，从而加快检索。
```sql
CREATE TABLE `t_person` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `extra` json DEFAULT NULL,
  `ft` varchar(255) GENERATED ALWAYS AS (json_extract(`extra`,'$.name')) VIRTUAL,
  PRIMARY KEY (`id`),
  KEY `idx_ft` (`ft`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
```

但是，virtual column 不支持全文检索！

# 参考

- [The JSON Data Type](https://dev.mysql.com/doc/refman/5.7/en/json.html)
- [JSON Functions](https://dev.mysql.com/doc/refman/5.7/en/json-functions.html)
- [MySQL JSON类型](https://www.jianshu.com/p/25161add5e4b)
- [Presentation : JSON improvements in MySQL 8.0](https://mydbops.wordpress.com/2019/02/26/presentation-json-improvements-in-mysql-8-0/)
