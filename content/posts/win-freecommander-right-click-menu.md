---
title: "修复 FreeCommander XE 右键菜单问题"
date: 2024-07-13T15:34:33+08:00
tags: ["windows"]
categories: ["windows"]
description: 
---

FreeCommander XE 是个好用又免费的多标签、双窗口文件管理器。
但是有个烦人的问题，右键菜单经常卡住无反应。

网上找到的解决方法：[Re: Right Click just Spins and Quits for No Context Menu in Win 10](https://freecommander.com/forum/viewtopic.php?t=10356#p38655)

修改配置文件：`C:\Users\<USERNAME>\AppData\Local\FreeCommanderXE\Settings\FreeCommander.ini`

```
after the line: Language=english.lng
add: ShowContextMenu64Bit=0
so it becomes:

[Form]
Language=english.lng
ShowContextMenu64Bit=0
MainMenuVisible=1
OneInstance=0
.....

Make sure you close FreeCommander before saving the changes
```

另外有一篇关于shell context菜单的问题帖子，记录下来：
[Fix Slow Right Click and Crashes Caused by Shell Extensions](https://www.winhelponline.com/blog/fix-slow-right-click-crashes-shell-extensions/)