---
title: centos7安装docker
date: 2020-01-07 18:13:42
tags: [docker, centos, linux, devops]
categories: [linux]
keywords: [centos7 docker]
description: 在centos7上安装docker。
---

在centos7上安装docker，中间遇到点问题，记录最后解决方式。
<!-- more -->

# 安装docker

```bash
# 添加阿里云repo
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

# 清理yum缓存
yum clean all

# 重建yum本地缓存
yum makecache fast

# 更新依赖
yum update --skip-broken

# 安装前置依赖
yum install -y yum-utils device-mapper-persistent-data lvm2

yum install docker-ce -y
```

之前切换yum源之后没有update，导致出错：
```bash
[root@host143 ~]# sudo yum install  containerd.io
已加载插件：fastestmirror, langpacks
Loading mirror speeds from cached hostfile
正在解决依赖关系
--> 正在检查事务
---> 软件包 containerd.io.x86_64.0.1.2.10-3.2.el7 将被 安装
--> 正在处理依赖关系 container-selinux >= 2:2.74，它被软件包 containerd.io-1.2.10-3.2.el7.x86_64 需要
--> 解决依赖关系完成
错误：软件包：containerd.io-1.2.10-3.2.el7.x86_64 (docker-ce-stable)
          需要：container-selinux >= 2:2.74
 您可以尝试添加 --skip-broken 选项来解决该问题
```

# 安装docker-compose

安装python3
```bash
yum -y install zlib-devel bzip2-devel openssl-devel openssl-static ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel libffi-devel lzma gcc

cd /usr/local/src
wget https://www.python.org/ftp/python/3.7.2/Python-3.7.2.tgz
tar xvf Python-3.7.2.tar.xz 
cd Python-3.7.2/
./configure --prefix=/usr/local/sbin/python-3.7
make && make install

ln -sv /usr/local/sbin/python-3.7/bin/python3 /usr/bin/python3
```

先安装pip。
```bash
yum install -y python34-pip
pip3 install --upgrade pip3
```

为了加速，设置全局的国内pip源。
在用户根目录新建`~/.pip/pip.conf`
```ini
[global]
index-url=https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

安装docker-compose
```
pip3 install -y docker-compose
```