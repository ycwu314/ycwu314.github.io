---
title: "S3 杂七杂八汇总"
date: 2023-12-19T11:04:52+08:00
draft: false
tags: ["self-hosted", "s3"]
categories: ["self-hosted"]
description: 整理最近折腾S3的资料。
---

最近逐步把自建服务对接到S3做为数据源或者备份，记录下。

自建服务，优先考虑原生支持S3存储，其次是通过webdav挂载S3存储。

但是webdav挂载有缺陷，不是完整支持posix语义，比如软连接、随机读取，另外还有缓存数据问题（vfs相关，以后单独整理）。


# S3供应商

S3供应商很多。考虑的是容量和流量，体验一圈候选的有：

## b2

免费10GB存储。对接cf的话流量免费。超出后使用费也比较可以。

## 群晖c2

1个区域免费15GB，共有3个区域（tw、us、eu），也就是45GB免费。每月流量15GB免费。收费计划 70u TB/year。

## cloudflare r2


>存储费用：每个月10GB免费额度，超出后每个月每 GB 收取 $0.015 的存储费用
>
>A 类操作费用：每个月一百万次免费额度，超出后每百万次收取 $4.50 的操作费用
>
>B 类操作费用：每个月一千万次免费额度，超出后每百万次收取 $0.36 的操作费用 



# 挂载S3存储

最初参考了JuiceFS和其他对象存储的对比文档：
- https://juicefs.com/docs/zh/community/comparison/juicefs_vs_s3fs/
- https://juicefs.com/docs/zh/community/comparison/juicefs_vs_s3ql/
- https://juicefs.com/docs/zh/community/comparison/juicefs_vs_seaweedfs/

## s3fs-fuse

https://github.com/s3fs-fuse/s3fs-fuse

用起来比较简单。但是踩坑。

1. apt源的版本比较老v1.86，最新v1.93。有点问题。需要使用源码构建最新版本
2. 在宿主机挂载webdav良好。但是挂载到docker volumn，会有访问问题，不管是`fuse.conf`开启`user_allow_other `，还是`chmod 777`都不正常，导致查看不了文件列表。折腾半天没有解决，最终放弃了。

## rclone 

https://github.com/rclone/rclone

rclone支持多种存储挂载，非常舒服。

一开始也踩坑，vfs相关配置，导致添加文件后一直刷新不出来，后来根据官方文档调整缓存时间解决。

可以通过缓存s3到本地，从而支持随机读取。

最终使用rclone。

## s3ql

https://github.com/s3ql/s3ql

TODO。

## seaweedfs

https://github.com/seaweedfs/seaweedfs

分布式对象存储引擎，功能强大。可以作为gateway。单纯用来挂载s3就大材小用了。

## 其他

挂载s3到本地目录，使用了linxu的fuse文件系统。

默认`/etc/fuse.conf`是关闭不同用户共享挂载点，导致非root用户访问权限问题：

```conf
# user_allow_other - Using the allow_other mount option works fine as root, in
# order to have it work as user you need user_allow_other in /etc/fuse.conf as
# well. (This option allows users to use the allow_other option.) You need
# allow_other if you want users other than the owner to access a mounted fuse.
# This option must appear on a line by itself. There is no value, just the
# presence of the option.

user_allow_other

```

# 连接工具

## rclone

https://github.com/rclone/rclone

万金油的rclone。win下面没有好用的客户端，跑命令行更方便。

## RaiDrive

https://www.raidrive.com/

RaiDrive以前使用好一段时间。免费版限制比较多，广告烦人。付费版功能解锁不错，但是有点贵。

## cyberduck

https://cyberduck.io/

https://mountainduck.io/

>Cyberduck is a libre server and cloud storage browser for Mac and Windows with support for FTP, SFTP, WebDAV, Amazon S3, OpenStack Swift, Backblaze B2, Microsoft Azure & OneDrive, Google Drive and Dropbox.

提供win/mac客户端。

免费版就挺好用，功能齐全，支持的存储多样，没有烦人的广告，只是关闭软件时候会提醒donate，10u。

缺点是启动有点慢。

推荐！

## alist

万金油的，不多说了。可以直接暴露到web端。

https://github.com/alist-org/alist


## go-drive

一个新项目，比较小巧，可以关注后续发展。

https://github.com/devld/go-drive


