---
title: ubuntu软件包版本问题
date: 2019-05-31 17:57:41
tags: linux
categories: linux
---

和朋友业余捣鼓项目，继续全(zhe)栈(teng)的感觉。在前东家申请了企业免费试用后，买买买之后就是安装软件。
Ubuntu的包管理机制安装软件通常比较方便。但是软件版本可能不是想要的。例如Ubuntu 18.04默认的Nginx包版本是1.14，但是我想安装1.16。

查看软件包的版本

<!-- more -->
```bash
# apt-cache madison nginx
     nginx | 1.14.0-0ubuntu1.2 | http://mirrors.cloud.aliyuncs.com/ubuntu bionic-updates/main amd64 Packages
     nginx | 1.14.0-0ubuntu1.2 | http://mirrors.cloud.aliyuncs.com/ubuntu bionic-updates/main i386 Packages
     nginx | 1.14.0-0ubuntu1.2 | http://mirrors.cloud.aliyuncs.com/ubuntu bionic-security/main amd64 Packages
     nginx | 1.14.0-0ubuntu1.2 | http://mirrors.cloud.aliyuncs.com/ubuntu bionic-security/main i386 Packages
// 后面省略 
```
或者
```bash
# apt-cache policy nginx
```

要安装其他版本的Nginx，除了从官网下载源码构建，还可以切换软件包来源实现。
完整步骤参考Nginx官网 [nginx: Linux packages](https://nginx.org/en/linux_packages.html#Ubuntu)： 

设置stable的源（此时1.16是stable version）：
```bash
echo "deb http://nginx.org/packages/ubuntu `lsb_release -cs` nginx" \
    | sudo tee /etc/apt/sources.list.d/nginx.list
```

把nginx的签名安装到apt-key：
```bash
curl -fsSL https://nginx.org/keys/nginx_signing.key | sudo apt-key add -
```

接着更新apt和安装
```bash
sudo apt update
sudo apt install nginx
```

然而安装报错
```bash
Skipping acquire of configured file 'main/binary-i386/Packages' as repository 'xxx' doesn't support architecture 'i386'
```

找到一篇资料 [Skipping acquire of configured file 'main/binary-i386/Packages' as repository 'xxx' doesn't support architecture 'i386'](https://askubuntu.com/questions/741410/skipping-acquire-of-configured-file-main-binary-i386-packages-as-repository-x)，是因为安装包的arch问题，i386对应32bit，我的ecs是64bit，强制设置为amd64。
```bash
# cd /etc/apt/sources.list.d

# ll 
total 24
drwxr-xr-x 2 root root 4096 May 31 09:25 ./
drwxr-xr-x 7 root root 4096 May 31 09:23 ../
-rw-r--r-- 1 root root   64 May 31 09:25 nginx.list
-rw-r--r-- 1 root root  110 May 31 09:03 nodesource.list

# cat nginx.list 
deb http://nginx.org/packages/ubuntu bionic nginx
```bash
`nginx.list`修改为
```bash
deb [arch=amd64]  http://nginx.org/packages/ubuntu bionic nginx
```
再次安装即可。

这时再看看软件包版本
```bash
# apt-cache policy nginx
nginx:
  Installed: 1.16.0-1~bionic
  Candidate: 1.16.0-1~bionic
  Version table:
 *** 1.16.0-1~bionic 500
        500 http://nginx.org/packages/ubuntu bionic/nginx amd64 Packages
        100 /var/lib/dpkg/status
     1.14.2-1~bionic 500
        500 http://nginx.org/packages/ubuntu bionic/nginx amd64 Packages
// 后面省略
```
