---
title: "一加Ace2刷海外版rom"
date: 2023-11-20T15:07:03+08:00
description: 刷海外版rom，远离国产全家桶
---

想要个相对干净的手机，不要国产软件全家桶，不要动不动被反诈骗上报。

google pixel不错，但是价格略贵。
曲线救国路线是国内版手机，再刷海外版rom。

因此要：
1. 有对应海外版机型
2. 容易刷机

最终买了一加ace2。

上次刷机是android 4、5时代的事情。那时候卡刷包简单，现在反而是线刷简单。

网上很多教程都是解锁和root。对于刷海外版rom，不要求root。

# 选择rom

来自大佬整理的资料：

https://yun.daxiaamu.com/OnePlus_Roms/%E4%B8%80%E5%8A%A0OnePlus%20Ace%202/

>一加Ace2在海外销售的机型为11R（硬件相同），Ace2搭载系统为ColorOS，11R搭载系统为氧OS，两者可以互刷，因此本页面收录的系统包括ColorOS和氧OS，不按机型区分。
>
>PHK110=国行（ColorOS） CPH2487=海外（氧OS）

最终选择这个版本：
>氧OS CPH2487_13.1.0.582(EX01) A.43


# 刷机工具准备

一开始使用大侠阿木的一加全能工具包，体积略大，700+MB，而且启动缓慢。

后来发现只需要：
- usb驱动（区分高通、联发科），从全能工具包提取
- adb
- Fastboot Enhance

# 解锁和刷机步骤

这篇文章写的详细，不再重复：https://bbs.oneplus.com/thread/6269015

解锁流程：
- OEM 解锁
- 打开“USB 调试”
- 解锁bootloader

一定要先OEM解锁，再解锁bootloader！
解锁bootloader后，一旦解锁后，如果想重新上锁，要用原版rom！

刷机流程：
- Fastboot Enhance重启手机进入fastbootd模式
- 删除动态分区
- 从rom文件提取`payload.bin`
- 刷入`payload.bin`
- 重启手机，第一次重启比较久

这个过程，电脑不要断电、usb保持连接。

这里发生了小问题。刷机后重启，竟然提示输入密码(很奇怪，为什么要提示密码)，输入后又重启，无限repeat。

后来想是没有清理cache（因此提示输入密码）。

进入fastbootd模式，清理cache，重启即可。

# 系统体验

## 整体干净，但是。。。

干净。开机只见到google全家桶，还有oneplus全家桶。

然而，下载adguard配置拦截的时候，意外发现app列表怎么有pdd、uc等一大堆全家桶，并且桌面列表却没有显示！

可恶！删除干净，节省4GB存储。

## bug

锁屏后唤醒，一定概率自动亮度失效、屏幕很暗，外加指纹区域不唤醒。

