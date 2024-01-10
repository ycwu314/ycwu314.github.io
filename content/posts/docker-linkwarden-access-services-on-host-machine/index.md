---
title: "linkwarden连接本地chrome，增强爬取能力"
date: 2024-01-09T19:18:08+08:00
tags: ["linux", "docker", "self-hosted"]
categories: ["linux", "docker", "self-hosted"]
description: docker容器访问宿主机服务。
---

linkwarden 用着还可以，但是收藏infoq、zhihu文章就有麻烦：白屏、登录弹窗、广告太多等问题。

于是研究怎么提升 linkwarden 的爬取能力。

# linkwarden 源码分析

`/data/lib/api/archiveHandler.ts`
```js
export default async function archiveHandler(link: LinksAndCollectionAndOwner) {
  const browser = await chromium.launch();
```

修改为
```js
export default async function archiveHandler(link: LinksAndCollectionAndOwner) {
  const browser = await chromium.connectOverCDP("<chrome-remote-debug-addr>");
```

就可以使用外部的chrome进程爬取。然后配置chrome extension，就可以有屏蔽登录弹窗、广告过滤、阅读模式等能力。


# 方案分析

因为chrome消耗资源多，有ban机器风险（其实也多余，只要不一直跑），最初我在一台美国的vps上部署win + chrome，再给日本的vps部署linkwarden。但是美日网络不稳定，动不动30%的丢包率，于是放弃，只能考虑同一台vps上部署chrome和linkwarden。

为了在vps上顺利启动chrome，之前已经折腾了xfce4桌面、xrdp。

现在要解决linkwarden调用chrome的问题。

方案1：
- linkwarden以宿主机npm方式启动，连接本地的chrome。

优点：
- 不用解决复杂的网络问题
- 直接修改源文件启动即可

缺点：
- 要安装一大堆npm依赖、本地要安装pgsql
- 升级不方便
- vps迁移不够简单

方案2：

- docker容器部署的linkwarden，访问宿主机的chrome remote debug

优点：
- 升级方便
- vps迁移简单


于是采用方案2。

为了使docker能够正常访问宿主机服务，有2种常见的方式：
1. docker容器使用host网络模式
2. docker容器使用私有网络，但是打通和宿主机的通信

第一种比较简单，直接使用宿主机网络。
第二种相对复杂点，但是尽可能保留了网络隔离。

于是先尝试使用第二种方法。

# chrome remote debug 流量转发

chrome remote debug模式虽然提供了`--remote-debugging-address`，但是仅在`--headless`模式生效。

因此，直接使用 `--remote-debugging-address=0.0.0.0` 是不生效的。需要做流量转发到`localhost`才能生效。

流量转发有多种方式，对iptables不太熟悉，测试了几个写法也没有生效。直接使用`socat`解决。

```bash
socat TCP4-LISTEN:10000,reuseaddr,fork TCP4:127.0.0.1:9222
```

这里chrome远程调试端口为9222。本地暴露10000端口接受外部流量。

以nohup或者systemd service方式后台执行。`/etc/systemd/system/socat-proxy-9222.service`
```conf
[Unit]
Description=Socat Proxy Service 9222
After=network.target

[Service]
ExecStart=/usr/bin/socat TCP4-LISTEN:10000,reuseaddr,fork TCP4:127.0.0.1:9222
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable socat-proxy-9222
systemctl start socat-proxy-9222
systemctl status socat-proxy-9222
```

# docker 容器访问宿主机端口

本地环境：ubuntu 22.04 LTS， docker 1.24。

参考资料：[Docker容器如何优雅地访问宿主机网络](https://cloud.tencent.com/developer/article/2240955)

`host.docker.internal`是官方提供的容器访问宿主机的特殊域名。

官方介绍`host.docker.internal`，来源： https://docs.docker.com/desktop/networking/
>The host has a changing IP address, or none if you have no network access. We recommend that you connect to the special DNS name `host.docker.internal`, which resolves to the internal IP address used by the host.
>You can also reach the gateway using `gateway.docker.internal`.


如果使用`docker-compose.yaml`：
```yaml
services:
  xxx:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

进入容器，确实是看到了
```bash
root@b2f087637d42:/data# cat /etc/hosts                          
127.0.0.1       localhost
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
172.17.0.1      host.docker.internal
172.25.0.3      b2f087637d42
```


修改后的`archiveHandler.ts`丢进去容器
```js
export default async function archiveHandler(link: LinksAndCollectionAndOwner) {
  const browser = await chromium.connectOverCDP("http://host.docker.internal:10000");
```

```bash
docker cp /root/linkwarden/archiveHandler.ts linkwarden-linkwarden-1:/data/lib/api/ 
```

**重启容器生效**。


但是不能访问
```log
2024-01-08T06:52:15.455414560Z [1] Error processing link https://www.infoq.cn/article/j*6vP2PbUGGcRZBhcaog for user 1: browserType.connectOverCDP: Timeout 30000ms exceeded.
2024-01-08T06:52:15.455484235Z [1] =========================== logs ===========================
2024-01-08T06:52:15.455488714Z [1] <ws preparing> retrieving websocket url from http://host.docker.internal:10000
2024-01-08T06:52:15.455491960Z [1] ============================================================
2024-01-08T06:52:15.455494856Z [1]     at archiveHandler (/data/lib/api/archiveHandler.ts:24:34)
2024-01-08T06:52:15.455497681Z [1]     at archiveLink (/data/scripts/worker.ts:145:27)
2024-01-08T06:52:15.455500827Z [1]     at /data/scripts/worker.ts:166:17
2024-01-08T06:52:15.455503592Z [1]     at processBatch (/data/scripts/worker.ts:166:6)
2024-01-08T06:52:15.455506368Z [1]     at async init (/data/scripts/worker.ts:181:7) {
2024-01-08T06:52:15.455509143Z [1]   name: 'TimeoutError'
```

stackoverflow上的讨论
- [What is the equivalent of --add-host=host.docker.internal:host-gateway in a Compose file](https://stackoverflow.com/questions/70725881/what-is-the-equivalent-of-add-host-host-docker-internalhost-gateway-in-a-comp)

这个配置也确认了（默认不开启）：无效
>Make sure that `live-restore: false` otherwise `host.docker.internal` doesn't seem to work under Linux. 


这时想起会不会是防火墙问题？于是继续尝试。


# 防火墙

我的防火墙配置默认禁止所有
```bash
ufw default deny
```


为了简单，先停掉socat，用nc测试。宿主机上监听10000端口
```bash
ncat -l 1000 -k -c 'xargs -n1 echo'
```

进入容器测试10000端口，失败
```bash
nc -z -v host.docker.internal 10000
```

关闭防火墙，进入容器测试10000端口，成功了。
```bash
ufw disable
```


显然是网络接口联通性配置问题。

一开始想到到容器内的`/etc/hosts`文件
```
172.17.0.1      host.docker.internal
172.25.0.3      b2f087637d42
```
通过ufw尝试放开docker0网卡（默认为172.17.0.1）、容器网络gateway（172.25.0.1），再在容器内测试nc，不成功。


陷入死胡同。后来想应该考虑docker网络接口
```bash
# docker network ls
NETWORK ID     NAME                 DRIVER    SCOPE
bc9996e8693e   bridge               bridge    local
40365e96dd4c   host                 host      local
66f0d98e85d8   linkwarden_default   bridge    local
201d997ae2cb   none                 null      local
```


dcp启动的容器，使用了`linkwarden_default`私有网络，对应的网络接口是`br-`加上network id。
```bash
# ifconfig
br-66f0d98e85d8: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.25.0.1  netmask 255.255.0.0  broadcast 172.25.255.255
        inet6 fe80::42:1fff:fe77:3560  prefixlen 64  scopeid 0x20<link>
```

尝试允许通过网络接口 br-66f0d98e85d8 进入的流量访问本机的 10000 端口。
```bash
ufw allow in on br-66f0d98e85d8 to any port 10000
```

自动配置的方式
```bash
linkwarden_br=$(docker network ls | grep linkwarden_default | awk '{print $1}')
ufw allow in on br-${linkwarden_br} to any port 10000
```

重新开启防火墙，容器内测试nc成功了！
```bash
ufw enable
```


兴冲冲地关闭宿主机的nc、重新打开socat测试，可是失败了。
```log
2024-01-09T07:14:30.716402426Z [1] Error processing link https://www.zhihu.com/question/335007440/answer/769165264 for user 1: browserType.connectOverCDP: Unexpected status 500 when connecting to http://host.docker.internal:10000/json/version/.
2024-01-09T07:14:30.716433266Z [1] This does not look like a DevTools server, try connecting via ws://.
2024-01-09T07:14:30.716436832Z [1] =========================== logs ===========================
2024-01-09T07:14:30.716440089Z [1] <ws preparing> retrieving websocket url from http://host.docker.internal:10000
```

单独测试
```bash
# curl http://host.docker.internal:10000/json/version/
Host header is specified and is not an IP address or localhost.
```


一直以为是自己配置问题，结果更多人也遇到这个问题。`"for all platforms" is misleading`：

[From inside of a Docker container, how do I connect to the localhost of the machine?](https://stackoverflow.com/questions/24319662/from-inside-of-a-docker-container-how-do-i-connect-to-the-localhost-of-the-mach)

![host.docker.internal在linux上并不生效](host-docker-internal-linux.png)


不甘心，换成docker0网卡或者容器的gateway ip尝试，就成功了！于是把源码文件改为访问docker0 ip 地址。



# chrome 插件配置

playwright以隐身模式（incognito）启动chrome窗口。extension默认不允许在incognito模式使用。因此要先配置插件权限。

各种油猴插件。

# 最终方案： 以host网络模式启动docker容器

```yml
version: "3.9"
services:
  postgres:
    image: postgres:16-alpine
    env_file: .env
    restart: always
    volumes:
      - ./pgdata:/var/lib/postgresql/data
    network_mode: host

  linkwarden:
    deploy:
        resources:
            limits:
              cpus: "0.50"
    env_file: .env
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/postgres
    restart: always
    image: ghcr.io/linkwarden/linkwarden:v2.4.8
    volumes:
      - ./data:/data/data
    depends_on:
      - postgres
    network_mode: host
```

这样占用3000、5423端口。另外修改`DATABASE_URL`，pgsql连接地址为`localhost`。

linkwarden就能直接访问到宿主机的9222端口。

# 一些常用命令

容器
```bash
# 容器中安装调试工具
apt install -y net-tools iputils-ping netcat curl

nc -v host.docker.internal 2000
```

宿主机
```bash
# 监听端口，部署简单echo服务器
ncat -l 2000 -k -c 'xargs -n1 echo'

# 进入容器，执行命令
docker exec -it linkwarden-linkwarden-1 /bin/bash

# 查看容器日志
docker logs -t -f -n 30 linkwarden-linkwarden-1
```

