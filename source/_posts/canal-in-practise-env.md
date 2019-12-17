---
title: canal 使用环境问题记录
date: 2019-12-03 20:41:02
tags: [canal, kafka]
categories: [canal]
keywords: [canal binlog]
description: 记录2则环境问题导致canal不正常的case。
---

上个月使用canal，因为kafka配置、k8s mysql挂载配置问题导致canal异常，记录下来。
<!-- more -->

# kafka advertised.listeners

把canal部署到一台新的开发机器，启动报错。
```
2019-11-15 16:12:19.480 [pool-4-thread-1] ERROR com.alibaba.otter.canal.kafka.CanalKafkaProducer - java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.TimeoutException: Failed to update metadata after 60000 ms.
java.lang.RuntimeException: java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.TimeoutException: Failed to update metadata after 60000 ms.
        at com.alibaba.otter.canal.kafka.CanalKafkaProducer.produce(CanalKafkaProducer.java:215) ~[canal.server-1.1.4.jar:na]
        at com.alibaba.otter.canal.kafka.CanalKafkaProducer.send(CanalKafkaProducer.java:179) ~[canal.server-1.1.4.jar:na]
        at com.alibaba.otter.canal.kafka.CanalKafkaProducer.send(CanalKafkaProducer.java:120) ~[canal.server-1.1.4.jar:na]
        at com.alibaba.otter.canal.server.CanalMQStarter.worker(CanalMQStarter.java:183) [canal.server-1.1.4.jar:na]
        at com.alibaba.otter.canal.server.CanalMQStarter.access$500(CanalMQStarter.java:23) [canal.server-1.1.4.jar:na]
        at com.alibaba.otter.canal.server.CanalMQStarter$CanalMQRunnable.run(CanalMQStarter.java:225) [canal.server-1.1.4.jar:na]
        at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1142) [na:1.8.0_60]
```

一开始怀疑是producer client的Jar包版本与kafka集群版本不兼容（以前踩过坑，印象深刻）。但是查资料发现：

>在Kafka 0.10.2.0之前，Kafka服务器端和客户端版本之间的兼容性是“单向”的，即高版本的broker可以处理低版本client的请求。反过来，低版本的broker不能处理高版本client的请求。
>自0.10.2.0版本开始，社区对这个问题进行了优化——对于低版本broker + 高版本client(0.10.2.0)的环境而言，现在用户可以运行命令先查看当前broker支持的协议版本，然后再选择broker支持的最高版本封装请求即可。

kafka服务器是0.10.2.0，canal的kafka client是1.1.1。因此是兼容的。不过用测试命令发现：
```
[root@k8s-master bin]# ./kafka-broker-api-versions.sh --bootstrap-server localhost:9092
Exception in thread "main" java.lang.RuntimeException: Request METADATA failed on brokers List(localhost:9092 (id: -1 rack: null))
	at kafka.admin.AdminClient.sendAnyNode(AdminClient.scala:66)
	at kafka.admin.AdminClient.findAllBrokers(AdminClient.scala:90)
	at kafka.admin.AdminClient.listAllBrokerVersionInfo(AdminClient.scala:136)
	at kafka.admin.BrokerApiVersionsCommand$.execute(BrokerApiVersionsCommand.scala:42)
	at kafka.admin.BrokerApiVersionsCommand$.main(BrokerApiVersionsCommand.scala:36)
	at kafka.admin.BrokerApiVersionsCommand.main(BrokerApiVersionsCommand.scala)
```
kafka、canal是部署在同一台开发服务器。怀疑是配置问题：
kafka的`server.properties`配置如下
```
listeners=PLAINTEXT://<ip>:9092
advertised.listeners=PLAINTEXT://<ip>:9092
```
其中`<ip>`是开发服务器的ip地址。

- listeners： 真正监听的网络接口
- advertised.listeners： 对外暴露的网络接口，会注册到zookeeper

但是`canal.properties`
```
canal.mq.servers = 127.0.0.1:9092
```

把canal配置改为advertised.listeners的地址即可。

# mysql binlog position对齐

运行了2天，周一回来发现不能正常接收binlog了。
mysql部署在k8s上，然后k8s挂了！
重启k8s mysql，日志报错：
```
2019-11-19 11:22:58.844 [destination = example , address = /127.0.0.1:31503 , EventParser] ERROR com.alibaba.otter.canal.common.alarm.LogAlarmHandler - destination:example[java.io.IOException: Received error packet: errno = 1236, sqlstate = HY000 errmsg = Client requested master to start replication from position > file size
	at com.alibaba.otter.canal.parse.inbound.mysql.dbsync.DirectLogFetcher.fetch(DirectLogFetcher.java:102)
	at com.alibaba.otter.canal.parse.inbound.mysql.MysqlConnection.dump(MysqlConnection.java:235)
	at com.alibaba.otter.canal.parse.inbound.AbstractEventParser$3.run(AbstractEventParser.java:265)
	at java.lang.Thread.run(Thread.java:745)
```
binlog同步位置不对。打开k8s configmap，发现mysql binlog没有挂载在宿主机目录，重启后同步位置都没了😂。
从日志看，canal本地存储的position比mysql的binlog还大。
检查canal保存同步position：
```
[root@k8s-master conf]# cd example/
[root@k8s-master example]# ll
total 84
-rw-r--r-- 1 root root 73728 Nov 19 11:24 h2.mv.db
-rwxrwxrwx 1 root root  2092 Nov 18 11:05 instance.properties
-rwxr-xr-x 1 root root  2036 Nov 15 14:07 instance.properties.bak
-rw-r--r-- 1 root root   336 Nov 19 11:21 meta.dat

[root@k8s-master example]# cat meta.dat 
{"clientDatas":[{"clientIdentity":{"clientId":1001,"destination":"example","filter":""},"cursor":{"identity":{"slaveId":-1,"sourceAddress":{"address":"localhost","port":31503}},"postion":{"gtid":"","included":false,"journalName":"mysql-bin.000001","position":225115292,"serverId":1,"timestamp":1574093224000}}}],"destination":"example"}
```
因为是开发环境，直接把meta.dat清空。
正规来说，要把mysql binlog position更新回meta.dat。

重启canal，这下正常了。

# mysql reset master 导致同步异常

在写binlog相关操作文档，执行`reset master;`以后，binlog序号复位，从0开始。
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

后来发现canal报错了，example.log如下：
```
2019-12-17 15:01:42.374 [destination = example , address = /127.0.0.1:31503 , EventParser] ERROR com.alibaba.otter.canal.common.alarm.LogAlarmHandler - destination:example[java.io.IOException: Received error packet: errno = 1236, sqlstate = HY000 errmsg = Could not find first log file name in binary log index file
	at com.alibaba.otter.canal.parse.inbound.mysql.dbsync.DirectLogFetcher.fetch(DirectLogFetcher.java:102)
	at com.alibaba.otter.canal.parse.inbound.mysql.MysqlConnection.dump(MysqlConnection.java:235)
	at com.alibaba.otter.canal.parse.inbound.AbstractEventParser$3.run(AbstractEventParser.java:265)
	at java.lang.Thread.run(Thread.java:745)
```

> Could not find first log file name in binary log index file

很可能是同步水位问题。检查`conf/example/meta.dat`如下
```json
{
  "clientDatas": [
    {
      "clientIdentity": {
        "clientId": 1001,
        "destination": "example",
        "filter": ""
      },
      "cursor": {
        "identity": {
          "slaveId": -1,
          "sourceAddress": {
            "address": "localhost",
            "port": 31503
          }
        },
        "postion": {
          "gtid": "",
          "included": false,
          "journalName": "mysql-bin.000004",
          "position": 15570,
          "serverId": 1,
          "timestamp": 1576565961000
        }
      }
    }
  ],
  "destination": "example"
}
```

mysql已经重置了binlog，序号复位从0开始，删除了其他的binlog文件。但是canal没有同步更新，本地还是等待消费mysql-bin.000004，因此报错。
解决：
- 删除meta.dat

思考：
- 不要删除正在复制的binlog文件。

# 参考资料

- [Kafka协议兼容性改进](https://www.cnblogs.com/huxi2b/p/6784795.html)