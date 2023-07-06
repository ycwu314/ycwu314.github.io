---
title: mysql generated column
date: 2020-01-02 20:07:45
tags: [mysql]
categories: [mysql]
keywords: [mysql generated column]
description: mysql generated column支持Virtual和Stored两种模式，默认是Virtual。可以使用virtual + index 加速检索json type字段。
---

# 简介

mysql 5.7 提供了generated column生成特殊的列，该列的定义是一个函数。
mysql支持 Virtual Generated Column与Stored Generated Column。
<!-- more -->
```
column_name data_type [GENERATED ALWAYS] AS (expression)
   [VIRTUAL | STORED] [UNIQUE [KEY]]
```

`GENERATED ALWAYS`表明是generated column。

Virtual Generated Column保存在数据字典中（表的元数据），并不会将这一列数据持久化到磁盘上。
Stored Generated Column将会持久化到磁盘上，而不是每次读取的时候计算所得。
Stored模式会消耗更多的磁盘空间，默认使用的是Virtual。


# 例子1

外国人的名字 `full_name=first_name + last_name`，可以表示为：
```sql
CREATE TABLE contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    full_name varchar(101) GENERATED ALWAYS AS (CONCAT(first_name,' ',last_name)),
    email VARCHAR(100) NOT NULL
);
```


# 例子2

mysql 5.7.8以后支持了json类型。为了加速检索，可以为json内部的字段创建virtual generated column，再创建索引：
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
然后就可以在ft字段上创建索引了。
效果类似oracle的函数索引了。
但是目前generated column不支持全文索引。

对于virtual类型的衍生列，创建索引时，会将衍生列值物化到索引键里，即把衍生列的值计算出来，然后存放在索引里。
针对virtual类型的衍生列索引，在insert和update操作时会消耗额外的写负载。