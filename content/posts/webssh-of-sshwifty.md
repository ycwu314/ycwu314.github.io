---
title: "webssh工具之sshwifty"
date: 2023-12-28T17:41:35+08:00
tags: ["self-hosted"]
categories: ["self-hosted"]
description: 部署webssh工具，随时随地访问vps。
---

因为经常在不同设备访问vps，每次安装客户端、配置登录信息，有点繁琐，于是考虑部署网页版方案。

# noVNC or webssh

noVNC是h5 vnc客户端，需要在各个vps部署vnc客户端，更新nginx配置。

webssh则直接通过浏览器访问SSH，不需要客户端机器改造。

于是选择webssh。

webssh方案

- https://github.com/billchurch/webssh2
- https://github.com/huashengdun/webssh
- https://github.com/nirui/sshwifty

最后选用 sshwifty ， 因为它支持Presets预先配置好一堆连接信息。

# 安装

首先看下配置文件

https://github.com/nirui/sshwifty?tab=readme-ov-file#configuration-file


## 配置文件 `sshwifty.conf.json`

由于我使用密钥登录，所以选择`Private Key`。根据官方文档，使用`file://`方式传入密钥文件。

对外暴露8182端口。

```json
{
  "HostName": "",
  "SharedKey": "",
  "DialTimeout": 5,
  "Socks5": "",
  "Socks5User": "",
  "Socks5Password": "",
  "Servers": [
    {
      "ListenInterface": "0.0.0.0",
      "ListenPort": 8182,
      "InitialTimeout": 3,
      "ReadTimeout": 180,
      "WriteTimeout": 180,
      "HeartbeatTimeout": 20,
      "ReadDelay": 10,
      "WriteDelay": 10,
      "TLSCertificateFile": "",
      "TLSCertificateKeyFile": "",
      "ServerMessage": "Programmers in China launched an online campaign against [implicitly forced overtime work](https://en.wikipedia.org/wiki/996_working_hour_system) in pursuit of balanced work-life relationship. Sshwifty wouldn't exist if its author must work such extreme hours. If you're benefiting from hobbyist projects like this one, please consider to support the action."
    }
  ],
  "Presets": [
    {
      "Title": "cloudcone us",
      "Type": "SSH",
      "Host": "xxx.xxx.xxx.xxx:22",
      "Meta": {
        "User": "root",
        "Encoding": "utf-8",
        "Private Key": "file:///home/sshwifty/id_ed25519",
        "Authentication": "Private Key"
      }
    }  
  ],
  "OnlyAllowPresetRemotes": false
}
```

## docker

```shell
docker run --detach \
  --restart always \
  --publish 8182:8182 \
  --name sshwifty \
  -v /root/sshwifty:/home/sshwifty \
  --env SSHWIFTY_CONFIG=/home/sshwifty/sshwifty.conf.json \
  niruix/sshwifty:latest
```

环境变量`SSHWIFTY_CONFIG`指定配置文件。

通过映射方式挂载外部配置文件。

注意配置文件中使用的`Private Key`是映射后容器内的路径。

## nginx

```conf
  server_name xxxx;
      location / {
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header Host $http_host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header Range $http_range;
          proxy_set_header If-Range $http_if_range;            
          proxy_redirect off;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";           
          
          proxy_pass http://127.0.0.1:8182;
      }
```

## "TypeError: Cannot read property 'importKey' of undefined"

必须使用https。

https://github.com/nirui/sshwifty?tab=readme-ov-file#configuration-file


>It's usually because your web browser does not support WebCrypt API (such as window.crypto.subtle or anything under window.crypto), or the support has been disabled.
>
>If you're using Google Chrome, please connect Sshwifty with HTTPS. Chrome will disable WebCrypt and many other APIs when the connection is not safe.


# 已知问题

1. 不支持zmodem，因此使用rz和sz直接页面卡住
