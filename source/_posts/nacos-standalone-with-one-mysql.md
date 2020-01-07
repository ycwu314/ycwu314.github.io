---
title: nacos单机单数据库部署
date: 2020-01-07 19:51:48
tags: [nacos]
categories: [nacos]
keywords: [nacos mysql 单机部署]
description: nacos官方镜像的MYSQL_DATABASE_NUM参数设置为1，则支持单个mysql部署。
---

目前需要nacos单机模式+单个mysql的部署方案。
<!-- more -->
nacos官网（[Nacos Docker 快速开始](https://nacos.io/zh-cn/docs/quick-start-docker.html)）提供了docker-compose部署例子。
```
单机模式 Mysql

git clone https://github.com/nacos-group/nacos-docker.git
cd nacos-docker
docker-compose -f example/standalone-mysql.yaml up
```
但是发现`standalone-mysql.yaml`需要mysql部署master-slave，要提供2个mysql地址，具体见[standalone-mysql.yaml](https://github.com/nacos-group/nacos-docker/blob/master/example/standalone-mysql.yaml)，只填master会报错：
```
Caused by: java.lang.IllegalArgumentException: Could not resolve placeholder 'MYSQL_SLAVE_SERVICE_HOST' in value "jdbc:mysql://${MYSQL_SLAVE_SERVICE_HOST}:${MYSQL_SLAVE_SERVICE_PORT:3306}/${MYSQL_MASTER_SERVICE_DB_NAME}?characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true"
```

其实官网提供了一个控制参数
```
MYSQL_DATABASE_NUM	数据库数量	default :2
```
设置为1，则不需要提供slave的地址。

提供一份修改后的docker-compose文件作为参考，使用外部的mysql。
```yml
version: "2"
services:
  nacos:
    image: nacos/nacos-server:latest
    container_name: nacos-standalone-mysql
    environment:
      - PREFER_HOST_MODE=hostname
      - MODE=standalone
      - SPRING_DATASOURCE_PLATFORM=mysql
      - MYSQL_MASTER_SERVICE_HOST=xxx.xxx.xxx.xxx
      - MYSQL_MASTER_SERVICE_DB_NAME=nacos
      - MYSQL_MASTER_SERVICE_PORT=3306
      - MYSQL_MASTER_SERVICE_USER=nacos
      - MYSQL_MASTER_SERVICE_PASSWORD=nacos
      - MYSQL_DATABASE_NUM=1
    volumes:
      - /home/nacos/logs:/home/nacos/logs
      - /home/nacos/init.d/custom.properties:/home/nacos/init.d/custom.properties
    ports:
      - "8848:8848"
#    restart: on-failure
```

注意：
- 提前创建nacos数据库和建表语句
- compose文件的volumes： `<宿主机>:<容器>`。在宿主机建立对应文件夹，拷贝`custom.properties`文件。