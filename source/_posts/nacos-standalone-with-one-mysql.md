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

# docker compose naocs

nacos官网（[Nacos Docker 快速开始](https://nacos.io/zh-cn/docs/quick-start-docker.html)）提供了docker-compose部署例子。
```
# 单机模式 Mysql

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
其中：
- `SPRING_DATASOURCE_PLATFORM`: 指定数据源。默认情况下，standalone模式使用内嵌数据库。如果要在standalone模式下使用mysql，需要指定。

注意：
- 提前创建nacos数据库和建表语句
- compose文件的volumes： `<宿主机>:<容器>`。在宿主机建立对应文件夹，拷贝`custom.properties`文件。

# k8s nacos

更新于2020.5.8：
在开发环境使用k8s部署单节点的nacos server，当时忘记指定standalone模式，默认是cluster，导致服务发现功能不正常：
{% asset_img nacso-server-is-down.png nacso-server-is-down %}

容器内的启动脚本`docker-startup.sh`：
```bash
#===========================================================================================
# JVM Configuration
#===========================================================================================
if [[ "${MODE}" == "standalone" ]]; then

    JAVA_OPT="${JAVA_OPT} -Xms512m -Xmx512m -Xmn256m"
    JAVA_OPT="${JAVA_OPT} -Dnacos.standalone=true"
else

  JAVA_OPT="${JAVA_OPT} -server -Xms${JVM_XMS} -Xmx${JVM_XMX} -Xmn${JVM_XMN} -XX:MetaspaceSize=${JVM_MS} -XX:MaxMetaspaceSize=${JVM_MMS}"
  if [[ "${NACOS_DEBUG}" == "y" ]]; then
    JAVA_OPT="${JAVA_OPT} -Xdebug -Xrunjdwp:transport=dt_socket,address=9555,server=y,suspend=n"
  fi
  JAVA_OPT="${JAVA_OPT} -XX:-OmitStackTraceInFastThrow -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=${BASE_DIR}/logs/java_heapdump.hprof"
  JAVA_OPT="${JAVA_OPT} -XX:-UseLargePages"
  print_servers
fi
```


怀疑是cluster模式下NACOS_SERVERS配置有问题：
```
NACOS_SERVERS: nacos-0.nacos-center.v-base.svc.cluster.local.:30848
```

先改为单机模式，后续再研究。以下是修改后的k8s yaml
```yml
---
apiVersion: v1
kind: Service
metadata:
  name: nacos-center
  labels:
    app: nacos-center
  namespace: v-base
spec:
  ports:
    - port: 30848
      name: server
      targetPort: 30848
      nodePort: 30848
  selector:
    app: nacos
  type: NodePort
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nacos-cm
  namespace: v-base
data:
  mysql.master.db.name: "nacos"
  mysql.master.port: "3306"
  mysql.master.user: "xxx"
  mysql.master.password: "xxx"
  mysql.database.num: "1"
  mysql.master.service.host: "mysql.v-base"
  mode: "standalone"
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nacos
  namespace: v-base
spec:
  serviceName: nacos-center
  replicas: 1
  template:
    metadata:
      labels:
        app: nacos
      annotations:
        pod.alpha.kubernetes.io/initialized: "true"
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: "app"
                    operator: In
                    values:
                      - nacos-center
              topologyKey: "kubernetes.io/hostname"
      containers:
        - name: k8snacos
          imagePullPolicy: IfNotPresent
          image: xxx.com/base/nacos-server:1.1.4
          resources:
            limits:
              memory: "8Gi"
              cpu: "4000m"
            requests:
              memory: "1Gi"
              cpu: "1000m"
          ports:
            - containerPort: 30848
              name: client
          env: 
            - name: NACOS_REPLICAS
              value: "1"
            - name: SPRING_DATASOURCE_PLATFORM
              value: "mysql"
            - name: MODE
              valueFrom:
                configMapKeyRef:
                  name: nacos-cm
                  key: mode
            - name: MYSQL_MASTER_SERVICE_DB_NAME
              valueFrom:
                configMapKeyRef:
                  name: nacos-cm
                  key: mysql.master.db.name
            - name: MYSQL_MASTER_SERVICE_PORT
              valueFrom:
                configMapKeyRef:
                  name: nacos-cm
                  key: mysql.master.port
            - name: MYSQL_MASTER_SERVICE_USER
              valueFrom:
                configMapKeyRef:
                  name: nacos-cm
                  key: mysql.master.user
            - name: MYSQL_MASTER_SERVICE_PASSWORD
              valueFrom:
                configMapKeyRef:
                  name: nacos-cm
                  key: mysql.master.password
            - name: MYSQL_MASTER_SERVICE_HOST
              valueFrom:
                configMapKeyRef:
                  name: nacos-cm
                  key: mysql.master.service.host
            - name: MYSQL_DATABASE_NUM
              valueFrom:
                configMapKeyRef:
                  name: nacos-cm
                  key: mysql.database.num  
            - name: NACOS_SERVER_PORT
              value: "30848"
            - name: PREFER_HOST_MODE
              value: "hostname"
            - name: NACOS_SERVERS
              #value: "nacos-0.nacos-center.v-base.svc.cluster.local:8848 nacos-1.nacos-center.v-base.svc.cluster.local:8848 nacos-2.nacos-center.v-base.svc.cluster.local:8848"
              value: "nacos-0.nacos-center.v-base.svc.cluster.local.:30848"
  selector:
    matchLabels:
      app: nacos

```