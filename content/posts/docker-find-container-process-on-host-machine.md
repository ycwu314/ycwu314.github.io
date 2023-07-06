---
title: docker容器进程和宿主机进程映射
date: 2020-05-13 11:00:24
tags: [docker]
categories: [docker]
keywords: [docker ps, docker top]
description: docker容器内的一个进程对应于宿主机器上的一个进程。容器内的进程，与相对应的宿主进程，由相同的uid、gid拥有。
---

# 容器内进程和宿主机进程的映射

docker容器内的一个进程对应于宿主机器上的一个进程。
容器内的进程，与相对应的宿主进程，由相同的uid、gid拥有。
<!-- more -->

在k8s上部署nacos容器，下面演示怎么找到对应的宿主机进程。
```bash
# 找到nacos pod部署的机器
[root@master-29 ~]# kubectl describe pod nacos-0 -n v-base
Name:           nacos-0
Namespace:      v-base
Priority:       0
Node:           172.25.23.19/172.25.23.19


# ssh到目标宿主机
# 找到具体container id
[root@node-19 ~]# docker ps --filter name=nacos
CONTAINER ID        IMAGE                                    COMMAND                  CREATED             STATUS              PORTS               NAMES
d12fef39614c        ac34e13f83a8                             "bin/docker-startup.…"   15 hours ago        Up 15 hours                             k8s_k8snacos_nacos-0_v-base_f310006e-0798-42ca-852c-73a3784a9b47_0
0f885e4061d3        mirrorgooglecontainers/pause-amd64:3.1   "/pause"                 15 hours ago        Up 15 hours                             k8s_POD_nacos-0_v-base_f310006e-0798-42ca-852c-73a3784a9b47_0                                       k8s_POD_nacos-0_v-base_f310006e-0798-42ca-852c-73a3784a9b47_0


# docker top查看PID和PPID
# PID是容器内进程在宿主机上的pid
# PPID是容器内进程在宿主机上的父进程pid
# 注意和exec进入容器再执行top命令是不同的
[root@node-19 ~]# docker top d12fef39614c
UID                 PID                 PPID                C                   STIME               TTY                 TIME                CMD
root                13747               13727               0                   5月12                ?                   00:00:00            /bin/bash bin/docker-startup.sh
root                14001               13747               1                   5月12                ?                   00:15:03            /usr/lib/jvm/java-1.8.0-openjdk/bin/java -Xms512m -Xmx512m -Xmn256m -Dnacos.standalone=true -Dnacos.preferHostnameOverIp=true -Djava.ext.dirs=/usr/lib/jvm/java-1.8.0-openjdk/jre/lib/ext:/usr/lib/jvm/java-1.8.0-openjdk/lib/ext:/home/nacos/plugins/cmdb:/home/nacos/plugins/mysql -Xloggc:/home/nacos/logs/nacos_gc.log -verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps -XX:+PrintGCTimeStamps -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=10 -XX:GCLogFileSize=100M -Dnacos.home=/home/nacos -jar /home/nacos/target/nacos-server.jar --spring.config.location=classpath:/,classpath:/config/,file:./,file:./config/,file:/home/nacos/conf/,/home/nacos/init.d/ --spring.config.name=application,custom --logging.config=/home/nacos/conf/nacos-logback.xml --server.max-http-header-size=524288
root                26753               13727               0                   10:32               pts/0               00:00:00            bash


# 在宿主机上找到对应进程，验证PID和PPID
# ps -O 指定输出列
[root@node-19 ~]# ps ax -O uid,uname,gid,group,ppid | grep nacos
# 手动贴上header，方便比较
# PID   UID USER       GID GROUP     PPID S TTY          TIME COMMAND
14001     0 root         0 root     13747 S ?        00:15:04 /usr/lib/jvm/java-1.8.0-openjdk/bin/java -Xms512m -Xmx512m -Xmn256m -Dnacos.standalone=true -Dnacos.preferHostnameOverIp=true -Djava.ext.dirs=/usr/lib/jvm/java-1.8.0-openjdk/jre/lib/ext:/usr/lib/jvm/java-1.8.0-openjdk/lib/ext:/home/nacos/plugins/cmdb:/home/naco/plugins/mysql -Xloggc:/home/nacos/logs/nacos_gc.log -verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps -XX:+PrintGCTimeStamps -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=10 -XX:GCLogFileSize=100M -Dnacos.home=/home/nacos -jar /home/nacos/target/nacos-server.jar --spring.config.location=classpath:/,classpath:/config/,file:./,file:./config/,file:/home/nacos/conf/,/home/nacos/init.d/ --spring.config.name=application,custom --logging.config=/home/nacos/conf/nacos-logback.xml --server.max-http-header-size=524288
15857     0 root         0 root     30535 S pts/1    00:00:00 grep --color=auto nacos
```

# 在宿主机上根据进程PID查找归属容器ID

一台docker主机上跑了多个容器，可能其中一个容器里的进程导致了整个宿主机load很高。
先在宿主机上使用ps命令找到可疑的进程PID，然后执行：
```sh
for i in `docker ps -q`; do docker top $i  | xargs -i echo CONTAINER_ID=$i {} ; done | grep <PID>
```

其中：
- `docker ps -q`: 列出当前正在运行的容器ID
- `docker top <container_id>`: 容器内top情况
- `xargs -i echo CONTAINER_ID=$i {}`: 给每一行开头增加容器ID，方便`grep <PID>`后直接看到容器ID

# 扩展: ps命令的参数

ps命令看到的UID、GID，对应资料:
>0 用户ID(UID)：每个用户必需指定UID。UID 0是保留给root用户的，UID 1-99是保留给其它预定义用户的， UID 100-999是保留给系统用户的；
>0 组ID(GID)：主组ID(保存在/etc/group文件中)；

>ps a 显示现行终端机下的所有程序，包括其他用户的程序。
>ps f 用ASCII字符显示树状结构，表达程序间的相互关系。
>ps -H 显示树状结构，表示程序间的相互关系。
>ps e 列出程序时，显示每个程序所使用的环境变量。
>ps x 　显示所有程序，不以终端机来区分。


# 参考

- [Understanding how uid and gid work in Docker containers](https://medium.com/@mccode/understanding-how-uid-and-gid-work-in-docker-containers-c37a01d01cf)