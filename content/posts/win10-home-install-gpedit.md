---
title: "Win10 家庭版安装组策略 gpedit.msc"
date: 2024-03-12T10:34:33+08:00
tags: ["windows"]
categories: ["windows"]
description: windows 10 家庭版默认没有安装组策略，找到一个脚本可以安装。
---

1. 保存为`xxx.bat`

```bat
@echo off

pushd "%~dp0"

dir /b C:\Windows\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientExtensions-Package~3*.mum >List.txt

dir /b C:\Windows\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientTools-Package~3*.mum >>List.txt

for /f %%i in ('findstr /i . List.txt 2^>nul') do dism /online /norestart /add-package:"C:\Windows\servicing\Packages\%%i"

pause

```

2. 管理员权限打开cmd，再执行上面脚本


