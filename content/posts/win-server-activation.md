---
title: "Windows Server 激活"
date: 2023-11-30T10:28:55+08:00
tags: [windows]
categories: [windows]
description: WinServer服务器每隔几个小时就关机，最后发现是没有激活的原因。
---

# WinServer不定时关机

搞了便宜的4g3c vps。心心念念装了台win server小鸡。but，总是不定时关机。

一开始以为是母鸡上挤进了太多了mjj跑测试，不稳定，放几天看看。

一周过去还是老样子。查了资料才知道是未激活的原因。

# 升级和激活WinServer

vps安装的镜像是evaluate版本（评估版本，桌面右下角有提示）是不能直接激活的，要先升级为正式版本。

WinServer有standard和datacenter两个版本，根据需要在网上找到对应key。需要管理员权限：
```powershell
# 设置kms服务器
slmgr -skms skms.netnr.eu.org

# 升级为正式版，其中要重启
DISM /online /Set-Edition:ServerStandard /ProductKey:VDYBN-27WPP-V4HQT-9VMD4-VMK7H /AcceptEula

# 安装密钥 
slmgr -ipk VDYBN-27WPP-V4HQT-9VMD4-VMK7H

# 激活系统 
slmgr -ato
```

kms激活每间隔180天要验证。但保持联网，每7天会尝试续期。

# 参考

- [Windows Server 2016从Evaluation评估版转换成正式版](https://www.likecs.com/show-221350.html)
- https://kms.netnr.eu.org/?id=windows-server-2022

