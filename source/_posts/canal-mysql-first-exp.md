---
title: canal mysql 初体验
date: 2019-11-14 20:50:56
tags: [canal, mysql]
categories: [mysql]
keywords: [canal mysql binlog]
description: 使用canal解析mysql binlog。
---

# 背景

技术上的需求，要解析mysql binlog，再同步数据到elasticsearch。
<!-- more -->
一个简单的demo，使用canal接收mysql binlog日志，并且写入到kafka topic。新版的canal已经原生支持写入kafka、rocketmq，只需要配置即可，无需开发canal producer。
安装kafka、zookeeper、canal就不再重复了。

# 配置mysql

在`[mysqld]`开启binlog，**并且设置binlog_format为ROW**。
```
server-id               = 1
log_bin                 = /var/log/mysql/mysql-bin.log
expire_logs_days        = 10
max_binlog_size   = 100M
binlog_format = ROW
```

如果使用 statement 或者 mixed format，那么binlog里面只能看到sql语句，没有对应的数据。
修改配置后重启mysql
```
sudo systemctl start mysql.service
```

# 为canal创建mysql访问账号

嗯，这里我挖了坑。
create user之后grant all privilege，导致报错，详见后面的解析。

# 配置canal

`conf/canal.properties`是canal server的配置文件。
修改几个重要配置即可
```
# binlog filter config
canal.instance.filter.druid.ddl = true
canal.instance.filter.query.dcl = false
canal.instance.filter.query.dml = false
canal.instance.filter.query.ddl = false

canal.zkServers = 127.0.0.1

# tcp, kafka, RocketMQ
canal.serverMode = kafka

canal.mq.servers = 127.0.0.1:9092
```

`conf/example`下面的是canal client配置。
打开`instace.properties`
```
# position info
canal.instance.master.address=127.0.0.1:3306

# username/password
canal.instance.dbUsername=canal
canal.instance.dbPassword=canal

# table regex
#canal.instance.filter.regex=.*\\..*
canal.instance.filter.regex=user\\.t_person

# mq config
canal.mq.topic=binlog-test

```
包括了mysql服务器地址、canal连接mysql的账号、要同步的表、kafka topic等配置。

更多的配置见[Canal Kafka RocketMQ QuickStart](https://github.com/alibaba/canal/wiki/Canal-Kafka-RocketMQ-QuickStart)

# 启动canal

```
bin/startup.sh
```
canal server日志在`logs/canal/`，canal client日志在`logs/example/`。
观察发现client日志报错：
```
2019-11-14 16:29:57.529 [destination = example , address = /127.0.0.1:3306 , EventParser] ERROR c.a.o.c.p.inbound.mysql.rds.RdsBinlogEventParserProxy - dump address /127.0.0.1:3306 has an error, retrying. caused by
com.alibaba.otter.canal.parse.exception.CanalParseException: command : 'show master status' has an error!
Caused by: java.io.IOException: ErrorPacket [errorNumber=1227, fieldCount=-1, message=Access denied; you need (at least one of) the SUPER, REPLICATION CLIENT privilege(s) for this operation, sqlState=42000, sqlStateMarker=#]
 with command: show master status
        at com.alibaba.otter.canal.parse.driver.mysql.MysqlQueryExecutor.query(MysqlQueryExecutor.java:61) ~[canal.parse.driver-1.1.4.jar:na]
        at com.alibaba.otter.canal.parse.inbound.mysql.MysqlConnection.query(MysqlConnection.java:106) ~[canal.parse-1.1.4.jar:na]
```

因为canal server伪装为mysql slave，读取binlog二进制流来解析，因此需要replication的权限。
```sql
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'canal'@'%' IDENTIFIED BY 'canal';
```

重新grant之后，日志如下
```
2019-11-14 16:32:48.276 [destination = example , address = /127.0.0.1:3306 , EventParser] WARN  c.a.o.c.p.inbound.mysql.rds.RdsBinlogEventParserProxy - ---> begin to find start position, it will be long time for reset or first position
2019-11-14 16:32:48.277 [destination = example , address = /127.0.0.1:3306 , EventParser] WARN  c.a.o.c.p.inbound.mysql.rds.RdsBinlogEventParserProxy - prepare to find start position just show master status
2019-11-14 16:32:49.299 [destination = example , address = /127.0.0.1:3306 , EventParser] WARN  c.a.o.c.p.inbound.mysql.rds.RdsBinlogEventParserProxy - ---> find start position successfully, EntryPosition[included=false,journalName=mysql-bin.000001,position=4,serverId=1,gtid=<null>,timestamp=1573720110000] cost : 1014ms , the next step is binlog dump
```

插入一条sql
```sql
INSERT INTO `user`.`t_person` (`id`, `name`, `age`) VALUES ('1', '22', '3');
```

因为配置canal client写入kafka topic，直接查看
```
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic binlog-test --from-beginning

{"data":null,"database":"","es":1573720366000,"id":1,"isDdl":false,"mysqlType":null,"old":null,"pkNames":null,"sql":"GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'canal'@'%' IDENTIFIED WITH 'mysql_native_password' AS '*E3619321C1A937C46A0D8BD1DAC39F93B27D4458'","sqlType":null,"table":"","ts":1573720369373,"type":"QUERY"}
{"data":[{"id":"1","name":"22","age":"3"}],"database":"user","es":1573721530000,"id":2,"isDdl":false,"mysqlType":{"id":"int(11)","name":"varchar(255)","age":"int(11)"},"old":null,"pkNames":["id"],"sql":"","sqlType":{"id":4,"name":12,"age":4},"table":"t_person","ts":1573721530702,"type":"INSERT"}
```
第一条是grant的记录，是dcl语句。
第二条是刚刚插入的，是dml语句。
因为使用了canal.properties的默认配置，都放行了。后续可以在`# binlog filter config`加上过滤。

尝试delete效果
```
# mysql
INSERT INTO `user`.`t_person` (`id`, `name`, `age`) VALUES ('2', '33', '44');
DELETE FROM `user`.`t_person` WHERE ID > -1;

# kafka topic

{"data":[{"id":"1","name":"22","age":"3"},{"id":"2","name":"33","age":"44"}],"database":"user","es":1573736190000,"id":4,"isDdl":false,"mysqlType":{"id":"int(11)","name":"varchar(255)","age":"int(11)"},"old":null,"pkNames":["id"],"sql":"","sqlType":{"id":4,"name":12,"age":4},"table":"t_person","ts":1573736190235,"type":"DELETE"}
```
批量查询可以看到每条受影响的记录。这里要小心，如果批量删除的数据很大，会导致msg body很大。
考虑在应用层加上`limit`多删除几次。

# dcl，dml，ddl

canal可以根据sql语句类型，过滤binlog日志
- DML（data manipulation language）。操作数据相关，例如CRUD。
- DDL（data definition language）。table相关，例如create、drop、alter。
- DCL（Data Control Language）。权限、角色相关，例如grant。