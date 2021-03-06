---
title: Windows上切换多个java版本：java8和java11
date: 2019-07-18 10:19:01
tags: [java, 技巧]
categories: [java]
keywords: [多个java版本, java8, java11, setx /m, 查看java版本]
description: 使用setx命令修改windows的系统变量，切换多个java版本java8、java11。查看版本java -version
---

Windows上安装了java8和java11，时不时要切换，于是思考写行命令解决。
思路是修改java_home变量。我的java_home变量是设置在系统级别的。

修改环境变量有2个命令，set和setx：
- set：临时修改普通的环境变量，只对当前窗口有效。
- setx：可以永久修改环境变量，包括系统变量。不会影响已经打开的cmd窗口。

一开始饶了点弯路，用set不生效，后来才发现该用setx。

切换java8
```bat
setx /m JAVA_HOME "C:\Program Files\Java\jdk1.8.0_212"
```

切换java11
```bat
setx /m JAVA_HOME "C:\Program Files\Java\jdk-11.0.3"
```

其中`/m`参数表示修改系统变量。
分别保存为`java8.bat`和`java11.bat`。以管理员权限执行即可。唯一不足是打开时候cmd窗口闪屏，先凑合着使用。

切换后查看java版本
```
C:\Users\ycwu>java -version
java version "11.0.3" 2019-04-16 LTS
Java(TM) SE Runtime Environment 18.9 (build 11.0.3+12-LTS)
Java HotSpot(TM) 64-Bit Server VM 18.9 (build 11.0.3+12-LTS, mixed mode)
```

