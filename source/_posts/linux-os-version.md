---
title: linux查看os版本
date: 2020-05-20 09:46:33
tags: [linux]
categories: [linux]
keywords: [centos version]
description: 整理几个查看linux系统版本的方法。
---

几个查看liunx系统的方法。优先使用lsb_release。
<!-- more -->

# lsb_release

The lsb_release command displays `LSB (Linux Standard Base)` information about your specific Linux distribution, including version number, release codename, and distributor ID.

所有linux发行版都适用，但是要安装对应的lsb模块。

centos:
```sh
[root@host143 ~]# yum install -y redhat-lsb-core

[root@host143 ~]# lsb_release -a
LSB Version:	:core-4.1-amd64:core-4.1-noarch
Distributor ID:	CentOS
Description:	CentOS Linux release 7.5.1804 (Core) 
Release:	7.5.1804
Codename:	Core
```

ubuntu:
```sh
ubuntu@VM-0-2-ubuntu:~$ apt-get install lsb-core

ubuntu@VM-0-2-ubuntu:~$ lsb_release -a
LSB Version:	core-9.20170808ubuntu1-noarch:security-9.20170808ubuntu1-noarch
Distributor ID:	Ubuntu
Description:	Ubuntu 18.04.3 LTS
Release:	18.04
Codename:	bionic
```

# uname

能看到内核版本。
```sh
# ubuntu
ubuntu@VM-0-2-ubuntu:~$ uname -a
Linux VM-0-2-ubuntu 4.15.0-66-generic #75-Ubuntu SMP Tue Oct 1 05:24:09 UTC 2019 x86_64 x86_64 x86_64 GNU/Linux
```

# /proc/version

能够看到内核版本，不一定能够看到os version。
```sh
# ubuntu
ubuntu@VM-0-2-ubuntu:~$ cat /proc/version 
Linux version 4.15.0-66-generic (buildd@lgw01-amd64-044) (gcc version 7.4.0 (Ubuntu 7.4.0-1ubuntu1~18.04.1)) #75-Ubuntu SMP Tue Oct 1 05:24:09 UTC 2019

# centos
[root@host143 ~]# cat /proc/version 
Linux version 3.10.0-862.el7.x86_64 (builder@kbuilder.dev.centos.org) (gcc version 4.8.5 20150623 (Red Hat 4.8.5-28) (GCC) ) #1 SMP Fri Apr 20 16:44:24 UTC 2018
```

# /etc/issue

`/etc/issue`文件是Linux系统开机启动时在命令行界面弹出的欢迎语句文件
```sh
# 可能看到os version
ubuntu@VM-0-2-ubuntu:~$ cat /etc/issue
Ubuntu 18.04.3 LTS \n \l
```

# centos & redhat专属方式

```sh
# centos
[root@host143 ~]# rpm -q centos-release
centos-release-7-5.1804.el7.centos.x86_64

# redhat
# rpm -q redhat-release
```

```sh
# redhat, centos
[root@host143 ~]# cat /etc/redhat-release 
CentOS Linux release 7.5.1804 (Core)

[root@host143 ~]# cat /etc/centos-release
CentOS Linux release 7.5.1804 (Core)
```