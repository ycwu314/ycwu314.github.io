---
title: "Github ssh over https"
date: 2024-01-16T18:38:57+08:00
tags: ["linux"]
categories: ["linux"]
description: 开启ssh over https，解决防火墙屏蔽22端口问题。
---

git pull 的时候发现一直连接不上。

```
$ git pull
ssh: connect to host github.com port 22: Connection timed out
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.

```

一开始以为是great wall的问题，换了节点，都不成功。于是怀疑公司防火墙block了22端口。

查资料发现github支持使用443端口进行ssh： [Using SSH over the HTTPS port](https://docs.github.com/en/authentication/troubleshooting-ssh/using-ssh-over-the-https-port)


首先测试连通性
```bash
$ ssh -T -p 443 git@ssh.github.com
Hi xxx! You've successfully authenticated, but GitHub does not provide shell access.
```

没问题的话，`~/.ssh/config`添加配置
```
Host github.com
Hostname ssh.github.com
Port 443
```

最后`ssh -T -p 443 git@ssh.github.com`，测试连通性。