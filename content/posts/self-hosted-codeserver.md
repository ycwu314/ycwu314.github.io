---
title: "搭建 codeserver"
date: 2024-01-15T15:29:34+08:00
tags: ["self-hosted"]
categories: ["self-hosted"]
description: 随时随地搬砖
---

# 容器化部署后命令行安装扩展遇到的问题

为了方便迁移和构建codeserver环境，最先考虑的是容器化部署。
codeserver需要安装一堆扩展。在codeserver web安装没有问题，但是进入容器安装

```bash
/app/code-server/bin/code-server --install-extension redhat.java
```

执行成功，可是codeserver即使重启也没有正常识别出来。

自定义Dockerfile应该能解决，但是不想单独维护。

于是改为使用本地安装codeserver后，使用命令行再安装插件。

# 安装codeserver


```bash
curl -fsSL https://code-server.dev/install.sh | sh
```

这样可以自动安装服务：`/lib/systemd/system/code-server@.service`
```bash
[Unit]
Description=code-server
After=network.target

[Service]
Type=exec
ExecStart=/usr/bin/code-server
Restart=always
User=%i

[Install]
WantedBy=default.target
```

ps. 不要使用里面的脚本： https://coder.com/docs/code-server/latest/install#debian-ubuntu ，不会自动创建systemd service文件， 有个issue提到这事情，已经是2年前了。


配置文件：`~/.config/code-server/config.yaml`
```
bind-addr: 127.0.0.1:8080
auth: password
password: xxxx
cert: false
```

用户数据：`~/.local/share/code-server`



# 配置java环境

```bash
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"
```

查看支持的 java sdk 列表
```bash
sdk list java
```

再用`sdk install java <version>`安装。

```bash
sdk install java 17.0.9-oracle
```

默认安装路径：`${USER}/.sdkman/candidates`。稍后把路径配置到vscode的`settings.json`

安装maven
```bash
sdk install maven 3.9.6
```


# 安装扩展


为了能够正常安装vscode的原生扩展，需要手动添加地址。

在`/usr/lib/code-server/lib/vscode/product.json`增加内容
```bash
  "extensionsGallery": {
    "serviceUrl": "https://marketplace.visualstudio.com/_apis/public/gallery",
    "cacheUrl": "https://vscode.blob.core.windows.net/gallery/index",
    "itemUrl": "https://marketplace.visualstudio.com/items",
    "controlUrl": "",
    "recommendationsUrl": ""
  }
```



https://code.visualstudio.com/docs/editor/extension-marketplace

一定要安装`Extension Pack for Java`，好用。

选择一些工作上常用的扩展：
```bash
code-server --install-extension vscjava.vscode-java-pack
code-server --install-extension vmware.vscode-boot-dev-pack
code-server --install-extension redhat.fabric8-analytics

code-server --install-extension ms-azuretools.vscode-docker
code-server --install-extension ms-kubernetes-tools.vscode-kubernetes-tools
code-server --install-extension codezombiech.gitignore

```



# 配置 codeserver

vscode的配置文件路径：`~/.local/share/code-server/User/settings.json`


# TODO 

启动的时候偶尔看到这个错误，但暂未解决

```log
File not found: /usr/lib/code-server/lib/vscode/out/vsda_bg.wasm
File not found: /usr/lib/code-server/lib/vscode/out/vsda.js
```

