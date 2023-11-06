---
title: "Openwrt Magic Surf Network"
date: 2023-11-06T11:24:27+08:00
tags: [openwrt]
categories: [openwrt]
description: openwrt魔法上网。
---

这2天折腾openwrt魔法上网。
OpenClash界面过于复杂，而且折腾了半天还是各种问题，于是改用ShellClash。

ps. 还没整理完，就遇到clash全线404😂

# cpu架构体系

来源自 https://juewuy.github.io/bdaz/ ：

>uname -ms | tr ' ' '_' | tr '[A-Z]' '[a-z]'
>
>在返回的内容中即可看到CPU版本，之后找到对应版本的安装包或者内核即可
>
>aarch64=armv8=arm64
>
>华硕设备或小米R1D/R2D/R3D使用armv7内核可能无法运行，请尝试使用armv5内核
>
>mips设备通常都是mipsle-softfloat，如果无法运行，请逐一尝试其他mips内核

# 卸载OpenClash

```
opkg list_installed | grep openclash
opkg remove <openclash安装包>
```

中间可能报错提示，稍等一会执行即可：

>opkg_conf_load: Could not lock /var/lock/opkg.lock: Resource temporarily unavailable.


# 安装shellclash

参考了：https://blog.saky.site/post/shellclash/

但是有个问题，jsdelivr已经被墙，导致下载失败。经测试，找到另一个反代服务：https://gitmirror.com/raw.html

脚本修改成
```
wget --no-check-certificate -O /tmp/install.sh "https://raw.gitmirror.com/juewuy/ShellClash/master/install.sh" && sh /tmp/install.sh && source /etc/profile
```


# 文件路径、配置文件

选择安装root方式安装。

- 应用和配置在：/etc/clash
- 运行时文件、日志： /tmp、/tmp/ShellClash
- 规则文件： /etc/clash/yamls/config.yaml 。可以

# 切换内核

解压为标准二进制文件，通常无须改名，但务必保证文件名同时包含clash与linux两个字母且clash为首字母。丢到`/tmp`目录。


# dashboard和切换节点

clash服务成功启动后可以通过在浏览器访问 http://clash.razord.top 或者 https://yacd.haishan.me 来管理clash内置规则以及开启直连访问。
host为软路由ip，端口为9999，密钥为空。
but，当时电脑本地有小猫咪，劫持了 http://clash.razord.top 和 https://yacd.haishan.me ，导致一直登录失败。后来直接退出本地小猫咪才正常。

也可以直接使用ip访问： http://192.168.2.1:9999/ui/ 



# cpu温度获取

查看温度
```
cat /sys/devices/virtual/thermal/thermal_zone0/temp
```

`thermal_zoneX`: 多核cpu有多个温度文件。
温度单位是0.001℃

# 参考

- 常见问题： https://juewuy.github.io/chang-jian-wen-ti/
- 本地安装： https://juewuy.github.io/bdaz/

