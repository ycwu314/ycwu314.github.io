---
title: activiti 5.22 springboot2 集成
date: 2020-01-16 20:02:07
tags: [activiti, springboot]
categories: [activiti]
keywords: [activiti springboot2 集成]
description: activiti 5.22 springboot2 集成。
---

调研工作流引擎。先做acitviti 5.22的实验，记录集成springboot2的问题。
<!-- more -->

# application.yml

先贴上最终的yaml，后面是问题记录。
```yaml
spring:
  activiti:
    check-process-definitions: false #自动检查、部署流程定义文件
    database-schema-update: true #自动更新数据库结构
    #流程定义文件存放目录
    process-definition-location-prefix: classpath:/processes/
    #process-definition-location-suffixes: #流程文件格式

  datasource:
    url: jdbc:mysql://xxx.xxx.xxx.xxx:3306/activiti5?characterEncoding=UTF-8&useSSL=false
    username: zzz
    password: zzz
    driver-class-name: com.mysql.cj.jdbc.Driver

  jpa:
    database-platform: org.hibernate.dialect.MySQL5Dialect
    show-sql: true
    hibernate:
      ddl-auto: create
    generate-ddl: true
```

# hibernate dialect 问题

```
Caused by: org.hibernate.HibernateException: Access to DialectResolutionInfo cannot be null when 'hibernate.dialect' not set
	at org.hibernate.engine.jdbc.dialect.internal.DialectFactoryImpl.determineDialect(DialectFactoryImpl.java:100) ~[hibernate-core-5.4.9.Final.jar:5.4.9.Final]
```

设置`spring.jpa.database-platform`解决。

# hibernate 不能正常访问数据库

```
Caused by: org.springframework.beans.factory.BeanCreationException: Error creating bean with name 'processEngine': FactoryBean threw exception on object creation; nested exception is org.apache.ibatis.exceptions.PersistenceException: 
### Error querying database.  Cause: java.sql.SQLException: Access denied for user ''@'172.23.121.138' (using password: NO)
### The error may exist in org/activiti/db/mapping/entity/Property.xml
### The error may involve org.activiti.engine.impl.persistence.entity.PropertyEntity.selectDbSchemaVersion
### The error occurred while executing a query
### SQL: select VALUE_ from ACT_GE_PROPERTY where NAME_ = 'schema.version'
### Cause: java.sql.SQLException: Access denied for user ''@'172.23.121.138' (using password: NO)    
```

`spring.datasource`有2个账号设置：
- data-username 和 data-password ： Username of the database to execute DML scripts (if different). 专门用来执行dml语句。
- username 和 password： Login username of the database. 一般查询使用的账号。

最初配置了`data-username`，访问失败，改为`username`即可。

# 不能正常自动创建表

最初偷懒没有建立数据库表。设想开启了自动ddl，让jpa自动建表
```yaml
  jpa:
    database-platform: org.hibernate.dialect.MySQL5Dialect
    show-sql: true
    hibernate:
      ddl-auto: create
    generate-ddl: true
```
网上也有同样情况，springboot2上ddl不正常。
于是手动建表好了，不纠结。

# mysql 和 mysql55

自己建表，发现有个问题，activiti提供了mysql和mysql55两份sql。
查阅资料，对于mysql来说，版本低于 5.6.4的mysql不支持 带有毫秒精确度的timestamp和date类型。

低于 5.6.4版本的mysql需要执行如下脚本文件：
```
activiti.mysql55.create.engine.sql
activiti.mysql.create.identity.sql
activiti.mysql55.create.history.sql
```

版本号在5.6.4以及以上的mysql需要执行如下脚本
```
activiti.mysql.create.engine.sql
activiti.mysql.create.identity.sql
activiti.mysql.create.history.sql
```

# 屏蔽 SecurityAutoConfiguration

默认会启动SecurityAutoConfiguration，因为缺少security相关配置报错。
因为目前没有使用到，因此直接屏蔽。
```java
@SpringBootApplication(exclude = SecurityAutoConfiguration.class)
```