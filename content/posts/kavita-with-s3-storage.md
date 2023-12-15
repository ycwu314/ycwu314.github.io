---
title: "Kavita + S3 + rclone 搭建在线阅读器"
date: 2023-12-15T17:12:14+08:00
tags: ["self-hosted", "s3"]
categories: ["self-hosted"]
description: 方便随时阅读。
---

使用的设备有点多，访问电子书比较麻烦： 各个设备都安装软件，而且阅读进度不同步。

索性搭建在线阅读器。

# 阅读器方案

有3种可选方案：
1. vps + 远程桌面 + NeatReader
2. calibre-web
3. kavita

## 方案1

比较喜欢 NeatReader，支持格式多，阅读体验最友好。但是vps远程桌面体验受到网速影响大。

## 方案2

calibre-web 对书籍元数据支持好，但是阅读器体验好一般。一直不太喜欢。

calibre-web 安装后要指定数据库。

默认账号权限不开启在线阅读，要自行开启。

支持在线上传书籍。

参考： https://moyu.ee/p/calibre-web/

## 方案3

kavita对阅读漫画友好。电子书支持epub，pdf。作者很懒不支持azw。

https://feats.kavitareader.com/posts/54/azw-azw3-support

```
DESCRIPTION
as far as I can tell kavita does not support azw3

DECLINED
· 
Joe
This is not feasible due to lack of library support. Please use Calibre to convert to an appropriate format.
```

阅读器体验和 NeatReader 比较接近。

没有在线上传功能。

## 最终选择

kavita ， 阅读体验最重要。书籍管理直接丢去c2。

## 存储方案

考虑：
1. 优先免费存储，其次低成本付费存储
2. 容易挂载
3. 冷备

容量优先，对比了多个存储：
- synology c2支持免费15GB，可以使用3个区，支持s3；但是流量少每月15GB。
- b2 支持免费10GB，搭配cf无限流量。
- google drive，可以土区买便宜。

最终选择synology c2。 15GB不够用再说。

linux上支持挂载s3到本地目录的软件有很多。最初使用s3fs。

## s3fs

一开始在ubuntu 20.04 上使用`apt install -y s3fs`安装。
但是，仓库安装的版本很老 1.86，最新 1.94。老版本有些奇怪问题。于是手动编译安装。

参考：https://github.com/s3fs-fuse/s3fs-fuse/wiki/Installation-Notes

```shell
# the apt repo of s3fs version is really outdated
apt-get update || true
apt-get install -y build-essential git libfuse-dev libcurl4-openssl-dev libxml2-dev mime-support automake libtool
apt-get install -y pkg-config libssl-dev # See (*3)
cd /root
git clone https://github.com/s3fs-fuse/s3fs-fuse
cd /root/s3fs-fuse/
./autogen.sh
./configure --prefix=/usr --with-openssl # See (*1)
make & make install

s3fs --version

# enable allow others option
sed -i "s/#user_allow_other/user_allow_other/g" /etc/fuse.conf

```

通过fuse挂载文件系统容易产生权限问题。这里修改`fuse.conf`的`user_allow_other`。

然而，后面挂载到kavita，扫描书籍一直没有反应：
```
kavita    | [Kavita] [2023-12-14 09:18:52.916 +00:00  44] [Debug] API.Services.DirectoryService [ScanFiles] called on /ebook-library/艾萨克·阿西莫夫
kavita    | [Kavita] [2023-12-14 09:19:24.372 +00:00  43] [Information] API.Services.TaskScheduler A duplicate request for Library Scan on library 2 occured. Skipping
```

宿主机能够发现文件。进入容器也能访问到远程文件。但是kavita就是扫描不动。。。遂放弃。

## rclone

rclone也支持s3挂载。于是尝试。

```shell
apt update || true
apty install -y fuse3 
curl https://rclone.org/install.sh | sudo bash

# enable allow others option
sed -i "s/#user_allow_other/user_allow_other/g" /etc/fuse.conf
```


配置文件在`~/.config/rclone/rclone.conf`。

根据网上教程，使用`rclone config`命令操作即可。实际上是往`rclone.conf`写入类似配置：

```conf
[synology_us]
type = s3
provider = Synology
access_key_id = 
secret_access_key = 
region = 
endpoint = 
```


挂载s3到本地

```shell
rclone mount synology_us:ebook-library /mnt/ebook-library \
--no-checksum \
--use-server-modtime \
--no-gzip-encoding \
--no-seek \
--allow-other \
--allow-non-empty \
--cache-read-retries 15 \
--cache-db-purge \
--buffer-size 512M \
--dir-cache-time 1m \
--timeout 10m \
--vfs-cache-max-age 500h \
--vfs-read-ahead 1G \
--vfs-read-chunk-size 32M \
--vfs-cache-max-size 2G \
--vfs-cache-poll-interval 10s \
--vfs-cache-mode full  \
--poll-interval 10s \
--attr-timeout 10s \
--cache-dir=/tmp/rclone-cache \
--daemon

```

最初对vfs等配置不了解，直接copy网上的，遇到一个问题：

在群晖web添加文件后，服务器一直发现不了新文件！kill rclone进程重新挂载才能发现新文件。

最后官文档方发现是`--dir-cache-time`配置。网上copy了个500h的。

完整配置： https://rclone.org/commands/rclone_mount/#options

# kavita


```yml
version: "2.1"
services:
  kavita:
    image: lscr.io/linuxserver/kavita:latest
    container_name: kavita
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
    volumes:
      # add many library folder as you wish 
      - /mnt/ebook-library:/ebook-library
      # kavita config folder: /config or /app/kavita/config
      - ./data:/config     
    ports:
      - 5000:5000
    restart: unless-stopped
```

开始踩坑。

## kavita config 路径

网上的例子， `/kavita/config` 并不是配置文件（数据库、封面，etc）的存储路径。

容器内的路径是`/app/kavita/config`或者`/config`。

可以外部挂载这2个目录，备份 kavita 元数据。


## 目录结构

丢到bucket里面的epub文件一直识别不了。后来发现kavita对目录结构有要求，否则识别不了：

https://wiki.kavitareader.com/en/guides/managing-your-files/scanner

不要直接在根目录放置文件！

不要直接在根目录放置文件！

不要直接在根目录放置文件！

```
Library Root
  ┠── Series Name A
  │   ┠── Series Name A - v01.cbz
  │   ⋮
  │   ┠── Series Name A - v06.cbz
  │   ┖── Specials
  │     ┖── Artbook 1.cbz
  │
  ┖── Series Name B
      ┠── Series Name B - v01.cbz
      ⋮
      ┠── Series Name B - v06.cbz
      ┖── Specials
        ┖── Artbook 1.cbz

```

或者

```
Library Root
  ┠── Publisher A
  │   ┠── Series Name A
  │   │   ┠── Series Name A - v01.cbz
  │   │   ⋮
  │   │   ┖── Series Name A - v06.cbz
  │   │
  │   ┖── Series Name B
  │             ┖── Oneshot.cbz
  │
  ┖── Publisher B
      ┠── Series Name C
      │   ┠── Series Name C - v01.cbz
      │   ⋮
      │   ┖── Series Name C - v06.cbz
      │
      ┖── Series Name D
                ┖── Oneshot.cbz

```
