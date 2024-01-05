---
title: "Ubuntu 22.04 xfce4 环境安装chrome"
date: 2024-01-05T10:34:09+08:00
tags: ["linux"]
categories: ["linux"]
description: 为了增强 linkwarden 的抓取能力，安装linux桌面再折腾chrome。
---

# 安装chrome

```bash
apt install -y fonts-liberation libu2f-udev xdg-utils
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb
rm -f google-chrome-stable_current_amd64.deb
```

第一行的apt安装前置依赖，因为是xfce4环境，默认缺少以内容导致报错：
```
dpkg: dependency problems prevent configuration of google-chrome-stable:
 google-chrome-stable depends on fonts-liberation; however:
  Package fonts-liberation is not installed.
 google-chrome-stable depends on libu2f-udev; however:
  Package libu2f-udev is not installed.
 google-chrome-stable depends on xdg-utils (>= 1.0.2); however:
  Package xdg-utils is not installed.
```
如果是xubuntu-desktop桌面，则可以跳过。

# 配置chrome

因为是虚拟机环境使用，且配合linkwarden启动的playwright使用，对chrome进行了配置。

TODO
