---
title: elasticsearch客户端比较
date: 2020-02-25 16:48:55
tags: [elasticsearch]
categories: [elasticsearch]
keywords: [elasticsearch 客户端]
description: 简单比较几种常见的elasticsearch client。
---

# 背景

项目上考虑兼容es 2.x和es 7.x，于是调研了不同elasticsearch client，做下笔记。
<!-- more -->

# transport vs rest ?

elasticsearch client主要分为transport和rest两大类。

>So, what's the difference between these two APIs?  When a user sends a REST request to an Elasticsearch node, the coordinating node parses the JSON body and transforms it into its corresponding Java object.  From then on, the request is sent to other nodes in the cluster in a binary format -- the Java API -- using the transport networking layer.  A Java user uses the Transport Client to build these Java objects directly in their application, then makes requests using the same binary format passed across the transport layer, skipping the need for the parsing step needed by REST.

transport相比rest客户端，直接发送二进制序列化数据，省去json反序列化，性能好一点。
transport原生支持集群。

但是要连接多个不同版本的es node，transport容易出问题。

# transport client

优点：
- 能够使用ES集群中的一些特性
- 少了json到java object的反序列化过程，性能好一点点

缺点：
- JAR包版本需与ES集群版本一致，ES集群升级，客户端也跟着升级到相同版本

因为transport client的兼容性问题，官方逐渐淘汰并且建议迁移到rest client。
es 5.x 开始提供原生的rest client （high / low）。


# low level rest client

```xml
<dependency>
    <groupId>org.elasticsearch.client</groupId>
    <artifactId>elasticsearch-rest-client</artifactId>
    <version>7.2.1</version>
</dependency>
```

The low-level client’s features include:
- minimal dependencies
- load balancing across all available nodes
- failover in case of node failures and upon specific response codes
- failed connection penalization (whether a failed node is retried depends on how many consecutive times it failed; the more failed attempts the longer the client will wait before trying that same node again)
- persistent connections
- trace logging of requests and responses
- optional automatic discovery of cluster nodes

low level rest client 支持不同的es版本。但是不提供自动的数据组装，使用相对high level client繁琐一点。

# high level rest client

```xml
<dependency>
    <groupId>org.elasticsearch.client</groupId>
    <artifactId>elasticsearch-rest-high-level-client</artifactId>
    <version>7.2.1</version>
</dependency>
```

high level rest client基于low level封装，支持自动数据组装(marshalling和un-marshalling)。
high level提供major版本的兼容性。

兼容性：
>The High Level Client is guaranteed to be able to communicate with any Elasticsearch node running on the same major version and greater or equal minor version. It doesn’t need to be in the same minor version as the Elasticsearch nodes it communicates with, as it is forward compatible meaning that it supports communicating with later versions of Elasticsearch than the one it was developed for.

实际上高版本的high level client是可以连接到低版本的server，但是一些高级查询特性就不支持了。
实测使用7.2.1的high level client可以查询es 2 server。

# jest

jest是一个第三方的rest客户端，同样可以屏蔽es版本差异。在官方rest client出来之前是一个不错的选择。
```xml
<dependency>
    <groupId>io.searchbox</groupId>
    <artifactId>jest</artifactId>
    <version>6.3.1</version>
</dependency>
```

如果要使用QueryBuilder、Settings等类，需要引用ElasticSearch依赖，可能导致了跟版本依赖。但是不引用的话，手动拼接复杂query语句又很麻烦。
```java
<dependency>
    <groupId>org.elasticsearch</groupId>
    <artifactId>elasticsearch</artifactId>
    <version>${elasticsearch.version}</version>
</dependency>
```

# spring-data-elasticsearch

spring-data-elasticsearch也是rest client，尝试屏蔽版本差异。
底层基于high level client二次封装。但是对新版本es的支持落后很多。

# 小结

使用high level client去适配es2和es7，并且尽快推动es2升级es7。

# 参考

- [Java High Level REST Client Compatibility](https://www.elastic.co/guide/en/elasticsearch/client/java-rest/current/java-rest-high-compatibility.html)
- [elasticsearch 6.x 升级调研报告](https://zshell.cc/2018/03/24/elasticsearch--elasticsearch6.x%E5%8D%87%E7%BA%A7%E8%B0%83%E7%A0%94%E6%8A%A5%E5%91%8A/)
