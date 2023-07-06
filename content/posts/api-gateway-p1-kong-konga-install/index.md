---
title: API网关：kong和konga安装记录
date: 2020-07-31 16:21:50
tags: [kong, konga, API网关]
categories: [API网关]
keywords: [kong postgres konga]
description: kong和konga安装记录
---

kong 2.1.0、konga 0.14.9 with postgresql安装经历。
<!-- more -->

# postgres

安装pgsql 12.2
```
docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:12.3
```
为kong和konga分配用户和数据库：
```sql
CREATE USER kong with password 'kong';
CREATE DATABASE kong OWNER kong; 
grant all privileges on database kong to kong;


CREATE USER konga with password 'konga';
CREATE DATABASE konga OWNER konga; 
grant all privileges on database konga to konga;
```

接下来就开始翻车了。

# kong

参考官网：[Install Kong Gateway](https://konghq.com/install/?itm_source=website&itm_medium=nav)

## 安装和初始化

```
# 这里是centos7
# wget -O 指定输出的文件名
wget https://bintray.com/kong/kong-rpm/download_file?file_path=centos/7/kong-2.1.0.el7.amd64.rpm -O kong-2.1.0.el7.amd64.rpm

# localinstall指定安装本地rmp包
yum localinstall -y kong-2.1.0.el7.amd64.rpm
```

复制配置文件
```
cp /etc/kong/kong.conf.default /etc/kong/kong.conf
```
执行kong命令，都可以使用`-c`指定使用的配置文件。

kong支持检查配置
```
kong check <path/to/kong.conf>
```

## 放开管理端口

默认端口：
- Proxy 8000：接收客户端的 HTTP 请求，并转发到后端的 Upstream。
- Proxy 8443：接收客户端的 HTTPS 请求，并转发到后端的 Upstream。
- Admin 8001：接收管理员的 HTTP 请求，进行 Kong 的管理。
- Admin 8444：接收管理员的 HTTPS 请求，进行 Kong 的管理。

默认情况下，admin端口只允许本地访问（127.0.0.1）。根据实际需求修改kong.conf放开限制：
```ini
admin_listen = 0.0.0.0:8001 reuseport backlog=16384, 0.0.0.0:8444 http2 ssl reuseport backlog=16384
#admin_listen = 127.0.0.1:8001 reuseport backlog=16384, 127.0.0.1:8444 http2 ssl reuseport backlog=16384
```
修改后重启kong才生效。

## 数据库

kong也支持无数据库模式，但是production环境还是使用数据库靠谱。

修改kong.conf
```ini
database = postgres              # Determines which of PostgreSQL or Cassandra
                                 # this node will use as its datastore.
                                 # Accepted values are `postgres`,
                                 # `cassandra`, and `off`.

pg_host = xxx.xxx.xxx.xxx        # Host of the Postgres server.
pg_port = 5432                   # Port of the Postgres server.
#pg_timeout = 5000               # Defines the timeout (in ms), for connecting,
                                 # reading and writing.

pg_user =  kong                  # Postgres user.
pg_password = kong               # Postgres user's password.
pg_database = kong               # The database name to connect to.
```

初始化数据库
```
kong migrations bootstrap -c /etc/kong/kong.conf
```
kong官网说是支持postgres 9.5+，但是目前在pg 12.2上执行数据库初始化没有报错，也没有正常建表。
在pg 11.8是正常创建！


![kong-db.png](kong-db.png)




## 启动和测试

启动kong
```
kong start -c /etc/kong/kong.conf
```

测试kong，看到一堆输出，则正常启动了
```
curl 127.0.0.1:8001
```


# konga

此处省略一堆手动安装步骤，因为最后使用了docker部署。这里只保留验证postgres相关步骤。

konga支持的数据库：mysql，postgres，mongo。
konga使用sails做ORM框架，不支持postgres 12。2，经测试11.8是可以的。
konga需要初始化数据库
```sh
# var conString = "postgres://username:password@localhost/database";
node ./bin/konga.js  prepare --adapter postgres --uri postgresql://localhost:5432/konga
```
然后就报错了
```
error: A hook (`orm`) failed to load!
error: Failed to prepare database: error: column r.consrc does not exist
```

通过`package.json`，发现sails-postgres的版本是0.11.4，手动升级到1.0.2，结果waterline不兼容
```sh
[root@localhost konga]# npm install
[root@localhost konga]# npm start

> kongadmin@0.14.9 start /data/konga
> node --harmony app.js

A hook (`orm`) failed to load!
Error: 
-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
Cannot initialize Waterline.
The installed version of adapter `sails-postgresql` is too new!
Please try installing a version < 1.0.
-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

    at /data/konga/node_modules/waterline/lib/waterline.js:90:15
    at /data/konga/node_modules/waterline/node_modules/lodash/index.js:3073:15
    at baseForOwn (/data/konga/node_modules/waterline/node_modules/lodash/index.js:2046:14)
    at /data/konga/node_modules/waterline/node_modules/lodash/index.js:3043:18
    at Function.<anonymous> (/data/konga/node_modules/waterline/node_modules/lodash/index.js:3346:13)
    at module.exports.Waterline.initialize (/data/konga/node_modules/waterline/lib/waterline.js:86:7)
    at buildWaterlineOntology (/data/konga/node_modules/sails-hook-orm/lib/build-waterline-ontology.js:45:19)
    at Array.async.auto._buildOntology (/data/konga/node_modules/sails-hook-orm/lib/initialize.js:388:7)
    at listener (/data/konga/node_modules/sails-hook-orm/node_modules/async/lib/async.js:605:42)
    at /data/konga/node_modules/sails-hook-orm/node_modules/async/lib/async.js:544:17
    at _arrayEach (/data/konga/node_modules/sails-hook-orm/node_modules/async/lib/async.js:85:13)
    at Immediate.taskComplete (/data/konga/node_modules/sails-hook-orm/node_modules/async/lib/async.js:543:13)
    at runCallback (timers.js:705:18)
    at tryOnImmediate (timers.js:676:5)
    at processImmediate (timers.js:658:5)
    at process.topLevelDomainCallback (domain.js:120:23)
```

于是改为1.0.0以下的最高版本，0.12.2，还是不行。
```
A hook (`orm`) failed to load!
error: 字段 r.consrc 不存在
    at Connection.parseE (/data/konga/node_modules/sails-postgresql/node_modules/pg/lib/connection.js:539:11)
    at Connection.parseMessage (/data/konga/node_modules/sails-postgresql/node_modules/pg/lib/connection.js:366:17)
    at Socket.<anonymous> (/data/konga/node_modules/sails-postgresql/node_modules/pg/lib/connection.js:105:22)
    at Socket.emit (events.js:189:13)
    at Socket.EventEmitter.emit (domain.js:441:20)
    at addChunk (_stream_readable.js:284:12)
    at readableAddChunk (_stream_readable.js:265:11)
    at Socket.Readable.push (_stream_readable.js:220:10)
    at TCP.onStreamRead [as onread] (internal/stream_base_commons.js:94:17)
```

```
A hook (`orm`) failed to load!
/app/node_modules/sails-postgresql/lib/adapter.js:158
        var collection = connectionObject.collections[table];
                                          ^

TypeError: Cannot read property 'collections' of undefined
    at __DESCRIBE__ (/app/node_modules/sails-postgresql/lib/adapter.js:158:43)
    at after (/app/node_modules/sails-postgresql/lib/adapter.js:1292:7)
    at /app/node_modules/sails-postgresql/lib/adapter.js:1181:7
    at /app/node_modules/sails-postgresql/node_modules/pg/lib/pool.js:84:11
    at /app/node_modules/sails-postgresql/node_modules/pg/node_modules/generic-pool/lib/generic-pool.js:281:11
    at /app/node_modules/sails-postgresql/node_modules/pg/lib/pool.js:58:20
    at Connection.<anonymous> (/app/node_modules/sails-postgresql/node_modules/pg/lib/client.js:149:7)
    at Object.onceWrapper (events.js:417:26)
    at Connection.emit (events.js:322:22)
    at Connection.EventEmitter.emit (domain.js:482:12)
    at Socket.<anonymous> (/app/node_modules/sails-postgresql/node_modules/pg/lib/connection.js:109:12)
    at Socket.emit (events.js:310:20)
    at Socket.EventEmitter.emit (domain.js:482:12)
    at addChunk (_stream_readable.js:286:12)
    at readableAddChunk (_stream_readable.js:268:9)
    at Socket.Readable.push (_stream_readable.js:209:10)
    at TCP.onStreamRead (internal/stream_base_commons.js:186:23)
```

最后的存储方案：
- konga + mysql 5.7.30，适用于一般平台
- konga + postgresql 11.8，针对特定平台

konga的数据库表：


![konga-db.png](konga-db.png)



为了简化部署，把这两个存储的数据库ddl都dump下来。

因为konga的npm依赖包实在太多了，不适合做物理包部署，使用docker镜像部署：
```
docker run -d -p 1337:1337 -e "TOKEN_SECRET={{somerandomstring}}" -e "DB_ADAPTER=mysql" -e "DB_HOST=xxx.xxx.xxx.xxx" -e "DB_PORT=3306"  -e "DB_USER=konga" -e "DB_PASSWORD=konga" -e "DB_DATABASE=konga" -e "NODE_ENV=production" --name konga pantsel/konga
```
`TOKEN_SECRET`是jwt哈希时使用。
对外暴露1337端口。

然后打开konga，新建admin账号。
注意新建kong连接，填写的是admin端口（默认为8001 / 8444）：


![konga-new-connection.png](konga-new-connection.png)



