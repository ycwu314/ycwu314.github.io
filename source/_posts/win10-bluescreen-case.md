---
title: win10蓝屏处理case
date: 2020-07-09 10:01:12
tags: [故障案例, win10]
categories: [故障案例]
keywords: [win10 蓝屏]
description: 一次处理win10自动更新后蓝屏的案例。
---


上周bug 10自动更新后，时不时蓝屏，一天发生几次，不能正常使用了。
蓝屏代码是`WIN32K_POWER_WATCHDOG_TIMEOUT`。
<!-- more -->
触发时间点是待机，再唤醒就蓝屏了。
在巨硬官网没查到相应的处理方式。

查资料发现win10崩溃的时候会写下转存，存放在`C:\Windows\Minidump`，可以使用BlueScreenView这个软件查看。
{% asset_img win10-minidump.png %}

`ntoskrnl.exe`故障导致崩溃。查资料了解是计划任务程序，在空闲时间做内存压缩的。平时确实会闲置一会电脑，就突然卡一下。
参照 [ntoskrnl.exe占用cpu过高](http://blog.sina.com.cn/s/blog_ea9b83e30102yexr.html) 操作，禁止该计划任务。但是蓝屏照旧。

还是要从win10自动更新列表入手。发现更新了显卡驱动：
{% asset_img driver-update.png %}
先尝试更新驱动，从intel官网下载了27开头的最新驱动。
安装完后重启，目前1天多没再发生蓝屏。


