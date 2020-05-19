---
title: 使用nsenter访问docker容器
date: 2020-05-19 11:13:04
tags: [docker]
categories: [docker]
keywords: [docker nsenter]
description: dns容器通常没有shell环境，不能使用docker exec进入容器。可以使用nsenter访问容器。
---

# nsenter工具

nsenter可以在某个namespace下执行程序。默认执行的程序是`${SHELL}`。
<!-- more -->
常见参数有：
```
-t, --target pid
       Specify a target process to get contexts from.  The paths to the contexts specified by pid are>
       /proc/pid/ns/mnt    the mount namespace
       /proc/pid/ns/uts    the UTS namespace
       /proc/pid/ns/ipc    the IPC namespace
       /proc/pid/ns/net    the network namespace
       /proc/pid/ns/pid    the PID namespace
       /proc/pid/ns/user   the user namespace
       /proc/pid/root      the root directory
       /proc/pid/cwd       the working directory respectively

-m, --mount[=file]
       Enter  the  mount  namespace.  If no file is specified, enter the mount namespace of the target process.  If file is specified, enter the mount
       namespace specified by file

-u, --uts[=file]
       Enter the UTS namespace.  If no file is specified, enter the UTS namespace of the target process.  If file is specified, enter the  UTS  names‐
       pace specified by file

-i, --ipc[=file]
       Enter  the  IPC namespace.  If no file is specified, enter the IPC namespace of the target process.  If file is specified, enter the IPC names‐
       pace specified by file

-n, --net[=file]
       Enter the network namespace.  If no file is specified, enter the network namespace of the target process.  If file is specified, enter the net‐
       work namespace specified by file

-p, --pid[=file]
       Enter  the  PID namespace.  If no file is specified, enter the PID namespace of the target process.  If file is specified, enter the PID names‐
       pace specified by file

-U, --user[=file]
       Enter the user namespace.  If no file is specified, enter the user namespace of the target process.  If  file  is  specified,  enter  the  user
       namespace specified by file.  See also the --setuid and --setgid options.
```                

使用例子
```sh
PID=$(docker inspect --format {{.State.Pid}} <container_name_or_ID>)
nsenter --target $PID --mount --uts --ipc --net --pid
```

# 使用nsenter对dns容器抓包

dns容器通常不带shell环境，不能直接使用docker exec进入容器抓包。
可以使用nsenter切换到对应namespace，再使用tcpdump抓包。
```sh
# 窗口1
# 先找到容器id
[root@master-29 ~]# docker ps | grep coredns
67d08deccd40        7987f0908caf                                         "/coredns -conf /etc…"   8 days ago          Up 8 days                               k8scoredns_coredns-7c945697f5-8dd5n_kube-system_aa257a19-31a6-4bbb-8d8b-05804cf5f7a6_0
729bffc11526        mirrorgooglecontainers/pause-amd64:3.1               "/pause"                 8 days ago          Up 8 days                               k8s_POD_coredns-7c945697f5-8dd5n_kube-system_aa257a19-31a6-4bbb-8d8b-05804cf5f7a6_0

# 窗口1
# 使用docker inspect反查得到对应的PID
[root@master-29 ~]# docker inspect --format "{{.State.Pid}}" 67d08deccd40
176016

# 窗口1
[root@master-29 ~]# nsenter -n -t 176016

# 窗口2，切换到其他容器
# 因为dns容器有多个，nslookup指定使用的dns地址
# 此容器的 resolv.conf配置为 options ndots:5
bash-5.0# nslookup ycwu314.top 10.244.154.1 
Server:         10.244.154.1
Address:        10.244.154.1#53

Non-authoritative answer:
Name:   ycwu314.top
Address: 104.24.99.9
Name:   ycwu314.top
Address: 104.24.98.9
Name:   ycwu314.top
Address: 2606:4700:3033::6818:6309
Name:   ycwu314.top
Address: 2606:4700:3033::6818:6209

# 窗口1
# 抓包。dns默认使用udp协议、53端口
[root@master-29 ~]# tcpdump -i eth0 udp dst port 53 | grep ycwu314.top
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
# 先根据 options ndots配置，尝试发起本地dns查询
21:53:14.567215 IP 10.244.154.23.46946 > master-29.domain: 14770+ A? ycwu314.top.prophet.svc.cluster.local. (55)
21:53:14.568171 IP 10.244.154.23.36680 > master-29.domain: 49422+ A? ycwu314.top.svc.cluster.local. (47)
21:53:14.568910 IP 10.244.154.23.55443 > master-29.domain: 1651+ A? ycwu314.top.cluster.local. (43)
21:53:14.569494 IP 10.244.154.23.37613 > master-29.domain: 50249+ A? ycwu314.top. (29)
# 本地dns查询失败，发起外部dns查询
# 注意发起了A和AAAA记录查询
21:53:14.569812 IP master-29.36226 > xxx.com.domain: 50249+ A? ycwu314.top. (29)
21:53:14.571655 IP 10.244.154.23.34600 > master-29.domain: 19908+ AAAA? ycwu314.top. (29)
21:53:14.571867 IP master-29.36226 > xxx.com.domain: 19908+ AAAA? ycwu314.top. (29)
```

# options ndots 选项

从上面可以看到，k8s容器查询`ycwu314.top`，实际上依次发起了多次请求：
- ycwu314.top.prophet.svc.cluster.local.
- ycwu314.top.svc.cluster.local.
- ycwu314.top.cluster.local.
- ycwu314.top.

先发起了3次本地dns查询（`master-29.domain`），查询不到后再向外部dns服务器发起请求(`xxx.com.domain`)。因此整体查询dns延迟可能比较高。
`options ndots:5`表示域名包含`.`数量小于等于5个（并且不以`.`结尾），则认为是PQDN，会结合`domain`或者`search`的域名进行补全，再作为FQDN查询。


对应的性能优化：
1. 使用FQDN查询。
域名以`.`结尾，则resolver认为是FQDN，直接查询，而不使用`resolv.conf`中`domain`或者`search`选项进行补全。
例如：`ycwu314.top`是PQDN，`ycwu314.top.`是FQDN。

2. 修改ndots
比如`options ndots:1`。

```yml
apiVersion: v1
kind: Pod
metadata:
  namespace: default
  name: dns-example
spec:
  containers:
    - name: test
      image: nginx
  dnsConfig:
    options:
      - name: ndots
        value: "1"
```

# 参考

- [Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)