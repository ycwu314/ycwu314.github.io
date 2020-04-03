---
title: sql性能优化case 1
date: 2020-04-03 10:39:16
tags: [sql, 性能优化]
categories: [sql]
keywords: [sql 调优]
description: 一次sql优化经历。
---

# 背景

线上一个sql发生性能问题，炸锅了。超过40s都不能返回。
<!-- more -->

背景介绍：
1. VIDEODEV_INFO_VIEW是一张视图，转换底层的摄像机表
2. 摄像机使用“乐观锁”设计，包含一个version字段，对于update操作，不是修改原来记录，而是新增一条记录，且version自增。

VIDEODEV_INFO_VIEW的关键字段：
- ID：自增主键
- UUID：每个设备的UUID
- VIDEODEV_GB_ID：国标id
- ADMINAREA_GB_CODE：行政区划
- VERSION：当前版本号

sql的语义是：根据权限，拿到对应的设备信息。

```sql
SELECT
	A.* 
FROM
	VIDEODEV_INFO_VIEW A,
	( SELECT ID, Max( VERSION ) AS VERSION FROM VIDEODEV_INFO_VIEW GROUP BY ID ) B 
WHERE
	ADMINAREA_GB_CODE LIKE CONCAT ( 44, '%' ) 
	OR A.ID IN (
	8
	// 此处省略5000个id
	) 
	AND A.ID = B.ID 
	AND A.VERSION = B.VERSION 
GROUP BY
	A.UUID 
ORDER BY
	ID DESC 
	LIMIT 20
```

# 优化经历

## step 1

无脑explain一下：
```
| id | select_type | table            | partitions | type  | possible_keys                                                                               | key     | key_len | ref  | rows  | filtered | Extra                                           |
+----+-------------+------------------+------------+-------+---------------------------------------------------------------------------------------------+---------+---------+------+-------+----------+-------------------------------------------------+
|  1 | PRIMARY     | <derived2>       | NULL       | ALL   | NULL                                                                                        | NULL    | NULL    | NULL | 29096 |   100.00 | Using temporary; Using filesort                 |
|  1 | PRIMARY     | RM_VIDEODEV_INFO | NULL       | ALL   | PRIMARY,idx_RM_VIDEODEV_INFO_ver,index_ADMINAREA_GB_CODE                                    | NULL    | NULL    | NULL | 29096 |   100.00 | Range checked for each record (index map: 0x13) |
|  2 | DERIVED     | RM_VIDEODEV_INFO | NULL       | index | PRIMARY,idx_RM_VIDEODEV_INFO_ver,index_VIDEODEV_GB_ID,idx_bitmap_id,index_ADMINAREA_GB_CODE | PRIMARY | 4       | NULL | 29096 |   100.00 | NULL                                            |
```
29000的数据量，但是filesort、temp table。

一开始没认真对待，看到IN后面一堆id，怀疑是随机读太多，IO吃不消。
于是先把IN改成一个id，还是慢成狗。

## step 2

算了一下，前面的笛卡尔积，`29000 * 29000 = 841,000,000`。
尼玛，不跪才怪。

```sql
SELECT
	A.* 
FROM
	VIDEODEV_INFO_VIEW A,
	( SELECT ID, Max( VERSION ) AS VERSION FROM VIDEODEV_INFO_VIEW GROUP BY ID ) B 
```

这里有2个疑问：
1. 为什么要搞B表呢？
2. B表写的好别扭 

针对1），因为一个设备每个update修改版本都产生一条记录，因此要想办法拿到最新版本的那条记录。这是B表的出发点。
然而，B表这样写是有问题的
```sql
( SELECT ID, Max( VERSION ) AS VERSION FROM VIDEODEV_INFO_VIEW GROUP BY ID ) B 
```
ID是自增主键，肯定是不同的，`GROUP BY ID`这个操作完全没有意义！
设备的唯一标识不是ID，而是VIDEODEV_GB_ID，或者UUID。
这个错误的sql已经存在半年以上了。它虽然是错的，但是不影响最终结果😥。
正确写法是：
```sql
SELECT VIDEODEV_GB_ID, Max( VERSION ) AS VERSION FROM VIDEODEV_INFO_VIEW GROUP BY VIDEODEV_GB_ID 
```
另外，外围查询的`group by UUID`也是多余的😀。

## step 3

显然瓶颈在于关联，找到最大版本的记录。
那么为什么要搞多个version呢？问到原来的架构设计，说是避免并发插入的时候同时发生关联查询、导致锁表；因此引入version，实现乐观锁机制。

于是问了了解现场情况的同事，真实使用情况是，基本就是一个人操作，一次导入几千条数据。
以mysql的性能，单机1W左右的insert tps还是可以的。

version机制产生多条记录，可以通过定时器清除，减少数据量。但问题是，定时器不清理之前，会出现一个设备存在多条记录的问题。还是需要分组查询每个设备的最新版本信息。

个人觉得，version机制对于99%真实场景太重了。

那么，接下来解决问题的思路就有2个：
1. 整体代码去掉version机制，需要修改所有关联模块。
2. 兼容现有version机制

## 方案1

方案1的好处是一步到位，拨乱反正，把过度设计扭回来。
方案1的困难点在于牵扯了五六个模块，且开放了视图给外部系统使用。

方案1的改动：
- 应用层重写
- 修改这个sql
- 对外开放视图做兼容适配。保留version字段，但是永远为0。

因为`VIDEODEV_INFO_VIEW`每个设备只有一个记录，直接过滤就好。
```sql
SELECT
	A.*
FROM
	VIDEODEV_INFO_VIEW A
WHERE
	ADMINAREA_GB_CODE LIKE CONCAT ( 44, '%' ) 
	OR A.ID IN (
	8
// 省略4000个id
	) 
ORDER BY
	A.ID DESC 
	LIMIT 20
```
非常快，通常0.1s就能返回。

## 方案2

方案2不改动现在有问题的设计，只在sql上做优化。

假设VIDEODEV_INFO_VIEW上一个设备有多条记录。但是，**不需要每次都找出所有设备的最新版本**，只关注当前分页的设备即可。这样可以大大减少中间表数据，提升效率。
思路：
- 根据权限过滤VIDEODEV_GB_ID
- 去重，分页；得到最终的设备VIDEODEV_GB_ID (可能有多个version数据)，这是个小表。
- 再和原来的设备表做group by，得到最大version的行（即ID）
- 最后从VIDEODEV_INFO_VIEW表捞取对应表的记录。

```sql
SELECT A.*
FROM 
    (SELECT A.VIDEODEV_GB_ID,ba
         MAX( ID ) AS ID
    FROM 
        (SELECT DISTINCT VIDEODEV_GB_ID
        FROM VIDEODEV_INFO_VIEW A
        WHERE ADMINAREA_GB_CODE LIKE CONCAT ( 44, '%' )
                OR A.ID IN ( 
                    8, 10  // 省略一堆ID
                    )
        ORDER BY  VIDEODEV_GB_ID LIMIT 100, 20 ) C, VIDEODEV_INFO_VIEW A    // 分页
        WHERE C.VIDEODEV_GB_ID = A.VIDEODEV_GB_ID
        GROUP BY  A.VIDEODEV_GB_ID ) D, VIDEODEV_INFO_VIEW A
		WHERE D.ID = A.ID
```

针对29000的数据量，分页通常0.1s - 0.2s就能返回。
不分页查询，要5s才能返回。


# 小结

最终使用方案1。虽然改动大，但是一步到位修正旧的设计。
前人不考虑应用场景，引入sexy的过度设计，真是坑死后人。