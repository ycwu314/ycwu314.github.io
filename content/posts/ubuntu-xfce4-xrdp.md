---
title: "Ubuntu 22.04 安装xfce4桌面，以及开启xrdp"
date: 2024-01-05T10:34:09+08:00
tags: ["linux"]
categories: ["linux"]
description: 为了增强 linkwarden 的抓取能力，安装linux桌面再折腾chrome。
---


# 参考资料

- [让你的VPS拥有桌面环境（Ubuntu/Debian篇）](https://pickstar.today/2023/01/%E8%AE%A9%E4%BD%A0%E7%9A%84vps%E6%8B%A5%E6%9C%89%E6%A1%8C%E9%9D%A2%E7%8E%AF%E5%A2%83%EF%BC%88ubuntu-debian%E7%AF%87%EF%BC%89/)

根据上述大佬的文章操作。但还是遇到些问题，所以有了本次记录。

# 安装xfce4桌面


xubuntu-desktop包含xfce和其他工具包，更加开箱即用。

xfce4更加轻量，占用资源更少，但是可能缺少部分工具包。比如安装chrome的时候发现少了一些库，需要手动安装。

综合考虑，直接安装xfce4。

```bash
# xfce4
apt install xfce4 -y

# 启动时默认启动图形化桌面环境
systemctl set-default graphical.target

# 新建一个用户并赋予 sudo 权限用来登录桌面环境
useradd -d /home/truthseeker2077 -m truthseeker2077
passwd truthseeker2077
# 添加root权限
usermod -a -G sudo truthseeker2077
```

passwd只接受交互式输入密码。自动化工具中可以使用chpasswd修改用户密码；或者使用expect工具。
```bash
echo 'username:password' | chpasswd
```

# 安装和配置xrdp

```bash
apt install xrdp -y

# 默认情况下，Xrdp 使用 /etc/ssl/private/ssl-cert-snakeoil.key, 它仅仅对 “ssl-cert” 用户组成语可读。运行下面的命令，将 xrdp 用户添加到这个用户组
adduser xrdp ssl-cert  
```

更新`Xwrapper.config`(访问x11环境的用户权限)
```bash
vi /etc/X11/Xwrapper.config

#allowed_users=console

allowed_users=anybody
needs_root_rights=yes
```


创建`.xsession`配置文件，解决登录成功后就闪退
```bash
# 在 ssh 中使用需要被远程登录的账户
# echo xfce4-session >~/.xsession
echo xfce4-session > /home/truthseeker2077/.xsession
```


重启xrdp服务
```bash
systemctl restart xrdp
systemctl restart xrdp-sesman
```


# 开放端口

```bash
ufw allow 3389
```


ip白名单方式
```bash
iptables -A INPUT -p tcp --dport 3389 -s YOUR_IP -j ACCEPT
iptables -A INPUT -p tcp --dport 3389 -j DROP
```

# 常见错误

核心日志文件：
- /var/log/xrdp.log
- /var/log/xrdp-sesman.log

## xrdp_wm_log_msg: login failed for display 0

`/var/log/xrdp.log`
```log
[20240105-02:55:32] [WARN ] Cannot find keymap file /etc/xrdp/km-00000804.ini
[20240105-02:55:32] [WARN ] Cannot find keymap file /etc/xrdp/km-00000804.ini
[20240105-02:55:32] [INFO ] Loading keymap file /etc/xrdp/km-00000409.ini
[20240105-02:55:32] [WARN ] local keymap file for 0x00000804 found and doesn't match built in keymap, using local keymap file
[20240105-02:55:32] [INFO ] connecting to sesman ip 127.0.0.1 port 3350
[20240105-02:55:32] [INFO ] xrdp_wm_log_msg: sesman connect ok
[20240105-02:55:32] [INFO ] sesman connect ok
[20240105-02:55:32] [INFO ] sending login info to session manager, please wait...
[20240105-02:55:34] [INFO ] xrdp_wm_log_msg: login failed for display 0
[20240105-02:55:34] [INFO ] login failed for display 0
```


`/var/log/xrdp-sesman.log`
```log
[20240105-02:49:07] [INFO ] starting xrdp-sesman with pid 1534290
[20240105-02:53:04] [INFO ] Socket 8: AF_INET6 connection received from ::1 port 52180
[20240105-02:53:06] [ERROR] pam_authenticate failed: Authentication failure
[20240105-02:53:06] [INFO ] Username or password error for user: root
[20240105-02:53:06] [ERROR] sesman_data_in: scp_process_msg failed
```

可能的原因：
- 账号密码错误
- 账号密码错误，但是没有权限: xrdp访问ssl-cert；当前用户访问x11环境权限



## 登录成功后报错：something has gone wrong. A problem has occurred and the system can’t recover.

需要修复桌面环境
```bash
update-alternatives --config x-session-manager
```
根据安装情况选择。

## 闪退

`/var/log/xrdp-sesman.log`

```log
[20240105-03:47:54] [WARN ] Window manager (pid 1589394, display 11) exited with non-zero exit code 139 and signal 0. This could indicate a window manager config problem
[20240105-03:47:54] [WARN ] Window manager (pid 1589394, display 11) exited quickly (2 secs). This could indicate a window manager config problem
```


重启xrdp、xrdp-sesman、重启系统。


# `/etc/X11/Xwrapper.config`

（来自poe整理的资料）

`/etc/X11/Xwrapper.config` 是 X Window System的配置文件，它用于控制X服务器的启动和访问权限。让我们解析一下该配置文件的内容：

1. `allowed_users`：这一行指定了哪些用户可以启动X服务器。可能的值包括：

   - `console`：只允许本地控制台上的用户启动X服务器。
   - `anybody`：允许任何用户启动X服务器。
   - `root`：只允许root用户启动X服务器。

   默认情况下，该行设置为 `console`，这意味着只有本地控制台上的用户可以启动X服务器。

2. `needs_root_rights`：这一行指定是否需要root权限才能启动X服务器。可能的值包括：

   - `yes`：需要root权限才能启动X服务器。
   - `no`：不需要root权限。

   默认情况下，该行设置为 `no`，这意味着不需要root权限才能启动X服务器。

根据这些设置，Xwrapper.config 文件决定了谁可以启动X服务器以及是否需要root权限。

请注意，对 Xwrapper.config 文件的更改可能需要重新启动系统或重新启动相关的服务（如 Xorg 或 XRDP）才能生效。
