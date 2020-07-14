---
title: kubernates访问pod
date: 2019-09-29 14:26:41
tags: [kubernates]
categories: [kubernates]
keywords: [kubernates port-forward, kubernate pod nodeport]
description:
---

现在已经创建了一个tomcat的pod，接下来练习访问pod。
<!-- more -->
tomcat默认是8080端口提供服务。
```
kubectl run mytomcat --image=tomcat --port=8080
```
这里`--port`暴露容器的8080端口。

要想访问pod的8080端口，有多种方法。

# port-forward

通过端口转发映射本地端口到指定的应用端口。
```
## kubectl port-forward <pod_name> <local_port>:<container_port>

kubectl port-forward mytomcat-7d68ffdbfb-qbp6p 7001:8080
```
这里把本地7001端口映射到容器的8080端口。再使用`curl http://localhost:7001`测试返回。

# expose

把pod暴露为service。以service的方式提供对外访问。
```
kubectl expose deployment/mytomcat --type="NodePort" --port=7000 --target-port=8080
```
其中：
- `--port`是本地端口
- `--target-port`是容器暴露的端口

`type`有多个选项：
- ClusterIP： 通过集群的内部 IP 暴露服务，选择该值，服务只能够在集群内部可以访问，这也是默认的 ServiceType。
- NodePort： 通过每个 Node 上的 IP 和静态端口（NodePort）暴露服务。NodePort 服务会路由到 ClusterIP 服务，这个 ClusterIP 服务会自动创建。通过请求`<NodeIP>:<NodePort>`，可以从集群的外部访问一个 NodePort 服务。
- LoadBalancer： 使用云提供商的负载局衡器，可以向外部暴露服务。外部的负载均衡器可以路由到 NodePort 服务和 ClusterIP 服务。
- ExternalName： 通过返回 CNAME 和它的值，可以将服务映射到 externalName 字段的内容（例如， foo.bar.example.com）。 没有任何类型代理被创建，这只有 Kubernetes 1.7 或更高版本的 kube-dns 才支持

这里使用NodePort类型做实验。

执行`kubectl expose`之后，会新增一个service
```
# kubectl get svc
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
kubernetes   ClusterIP   10.152.183.1     <none>        443/TCP          25d
mytomcat     NodePort    10.152.183.222   <none>        7000:31364/TCP   69m
```

kubernates使用iptables创建了路由规则
```
# iptables-save | grep 10.152.183.222
-A KUBE-SERVICES ! -s 10.152.183.0/24 -d 10.152.183.222/32 -p tcp -m comment --comment "default/mytomcat: cluster IP" -m tcp --dport 7000 -j KUBE-MARK-MASQ
-A KUBE-SERVICES -d 10.152.183.222/32 -p tcp -m comment --comment "default/mytomcat: cluster IP" -m tcp --dport 7000 -j KUBE-SVC-GUOWFPQH6PYKZNE2
```

使用`curl http://<cluster-ip>:<port>`测试，成功返回首页内容
```
curl http://10.152.183.222:7000
```


# 参考

- [Use Port Forwarding to Access Applications in a Cluster](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/)




