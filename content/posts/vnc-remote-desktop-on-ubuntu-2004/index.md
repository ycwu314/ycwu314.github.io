---
title: ubuntu 20.04上使用vnc远程桌面连接
date: 2022-04-19 16:48:39
tags: [linux, kvm]
categories: [linux]
keywords: [vncserver]
description: ubuntu 20.04上使用vnc远程桌面连接。
---
使用向日葵远程到局域网内的ubuntu机器非常卡。于是搭建vncserver连接。
<!-- more -->

# 安装和配置vncserver

## 安装vncserver
```
sudo apt install xfce4 xfce4-goodies tightvncserver
```

## 配置防火墙规则
```
sudo ufw allow 5901/tcp
```

当使用VNC服务器时， `:X` 是一个引用的显示端口 `5900+X` 。
可以配置端口段，统一在防火墙放行。

## 修改xstarup配置文件

末尾增加startxfce4，登陆时启动xfce桌面。
```shell
(base) zj@zj-desktop:~$ vi ~/.vnc/xstartup
#!/bin/sh

xrdb $HOME/.Xresources
xsetroot -solid grey
#x-terminal-emulator -geometry 80x24+10+10 -ls -title "$VNCDESKTOP Desktop" &
#x-window-manager &
# Fix to make GNOME work
export XKL_XMODMAP_DISABLE=1
/etc/X11/Xsession
startxfce4
```

给当前用户增加访问权限
```
chmod u+x ~/.vnc/xstartup
```

## 设置分辨率

默认的分辨率(1024×768)比较低。

1. 单次修改
```
vncserver -geometry 1600x900
```

2. 全局修改
```
sudo vi /usr/bin/vncserver  
```
找到geometry
```
$geometry = “1600x900″; 
```
然后重启vncserver。

## 开启vncserver

配置vncserver密码
```
vncpasswd
```

开启一个远程桌面。
```shell
(base) zj@zj-desktop:~$ vncserver

New 'X' desktop is zj-desktop:1

Starting applications specified in /home/zj/.vnc/xstartup
Log file is /home/zj/.vnc/zj-desktop:1.log
```

删除指定的远程桌面号
```
vncserver -kill :1
```

# 客户端连接

远程连接是要提供地址的，这里的地址是`IP:桌面号`。
桌面号是`New 'X' desktop is zj-desktop:XXX`中的`XXX`。



![slug vnc-viewer-cfg.png](slug vnc-viewer-cfg.png)




# 常见问题

## 连接xfce桌面无法打开terminal终端

调整默认的终端应用。


![slug vnc-xfce-terminal.png](slug vnc-xfce-terminal.png)



## xfce中无法调整桌面分辨率



![slug xfce-config.png](slug xfce-config.png)



改为在vnc窗口启动时配置geometry。


## 调整xfce

Alt+鼠标右键+拖动。