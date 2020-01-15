---
title: nacos k8s mysql standalone 部署
date: 2020-01-15 18:27:07
tags: [nacos, kubernates]
categories: [nacos]
keywords: [nacos kuberates]
description: 部署nacos k8s standalone模式，使用单个mysql作为存储。
---

需要在开发环境部署nacos k8s。
<!-- more -->

基础yaml文件：[nacos-quick-start](https://github.com/nacos-group/nacos-k8s/blob/master/deploy/nacos/nacos-quick-start.yaml)。官方这个例子的效果是：
1. 仅在集群内部访问nacos
2. 3副本的nacos
3. 2节点的mysql

目前条件是：
1. 需要在k8s外部能够访问nacos控制台。且没有ingress服务。（使用NodePort方式暴露service）
2. 只要单节点的nacos即可。（修改`NACOS_REPLICAS`即可）
3. 现有k8s测试集群已经有单节点的mysql，能够满足开发需求，无需再部署。（需要修改配置）

针对3)，官方nacos-quick-start并不满足。要从镜像入手分析，对应镜像的ENV参数见[nacos-docker](https://github.com/nacos-group/nacos-docker)。
最后通过`mysql.database.num`实现只访问单节点的mysql。

完整的yaml文件如下：
```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: nacos-headless
  labels:
    app: nacos-headless
  namespace: v-base
spec:
  ports:
    - port: 8848
      name: server
      targetPort: 8848
      nodePort: 30848
  type: NodePort
  externalTrafficPolicy: Cluster
  selector:
    app: nacos
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nacos-cm
  namespace: v-base
data:
  mysql.master.db.name: "nacos"
  mysql.master.port: "3306"
  mysql.master.user: "nacos"
  mysql.master.password: "nacos"
  mysql.database.num: "1"
  mysql.master.service.host: "xxx.xxx.xxx.xxx"
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nacos
  namespace: v-base
spec:
  serviceName: nacos-headless
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
                      - nacos-headless
              topologyKey: "kubernetes.io/hostname"
      containers:
        - name: k8snacos
          imagePullPolicy: Always
          image: nacos/nacos-server:1.1.4
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
          ports:
            - containerPort: 8848
              name: client
          env: 
            - name: NACOS_REPLICAS
              value: "1"
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
              value: "8848"
            - name: PREFER_HOST_MODE
              value: "hostname"
            - name: NACOS_SERVERS
            #   value: "nacos-0.nacos-headless.default.svc.cluster.local:8848 nacos-1.nacos-headless.default.svc.cluster.local:8848 nacos-2.nacos-headless.default.svc.cluster.local:8848"
              value: "nacos-0.nacos-headless.default.svc.cluster.local:8848"
  selector:
    matchLabels:
      app: nacos
```