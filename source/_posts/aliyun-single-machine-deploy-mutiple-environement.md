---
title: 单个阿里云ECS部署多个环境的应用
date: 2019-08-04 12:49:55
tags: [devops, 技巧, 小程序, springboot]
categories: [devops]
keywords: [application-dev.properties, spring.profiles.active, kill -15]
description: 阿里云ECS上同时部署开发和生产的springboot应用。application-dev.properties存放开发环境。应用参数--spring.profiles.active=dev读取开发环境配置。使用kill -15关闭旧应用。
---

因为刚起步，小程序项目规模小，本着勤俭持家(qiong)的原则，我的java应用在一个阿里云ECS上部署开发环境和生产环境。

# 端口规划

首先要考虑Java应用端口规划
- 8000：生产环境
- 9000：开发环境

同时在ECS上配置安全组规则，放开端口。

# nginx配置

小程序生产环境要求https。但是开发环境可以在“项目设置”里面选择“不校验安全域名、TLS 版本以及 HTTPS 证书”，直接使用http方式。
因此直接暴露9000端口，不用原有nginx配置。

因为nginx上做了http到https的301强制改写，因此小程序上开发环境直接使用ip加端口访问。

# 中间件配置划分

mysql，redis等配置划分2份，没什么好说的

# spring boot配置文件支持多环境配置

用diamond之类可以方便管理多个环境配置。但是需要格外部署一个中间件，暂时不折腾。
spring boot的profiles机制对多环境配置提供了支持，现阶段使用没有问题。

application配置文件规划如下
- application.properties: 公共配置，例如各种超时配置
- application-local.properties：本地环境专有配置，例如mysq、redis。
- application-dev.properties：开发环境专有配置
- application-prod.properties：生产环境专有配置

启动的时候增加应用参数，是Program Arguments，并且是`--`，比如
```
--spring.profiles.active=local
```
{% asset_img v1_idea_springboot_profiles.png "springboot profiles" %}

# 更新云效流水线部署脚本

这个应用使用云效的流水线模式部署。

1. 登录云效，选择要修改的流水线环境，比如“日常环境”

2. 进入修改页面，点击“日常”
{% asset_img v1_编辑流水线.png 编辑流水线 %}

3. 查看部署配置
{% asset_img v1_流水线查看部署配置.png 流水线查看部署配置 %}

4. 在部署配置页面更新脚本
{% asset_img v1_云效流水线部署配置.png 云效流水线部署配置 %}


部署配置涉及打包文件存放路径，以及解压缩和执行应用。不同环境的打包文件存放在单独路径。这里提供一份参考
```bash
set -e;
THIS_ENV=dev
BASE_DIR=/home/admin/${THIS_ENV}
mkdir -p ${BASE_DIR}/medical
rm -f ${BASE_DIR}/medical/medical.jar
tar xf ${BASE_DIR}/package.tgz -o -C ${BASE_DIR}/medical;
${BASE_DIR}/deploy_medical.sh ${THIS_ENV} start
```
最后调用部署脚本是`deploy_medical.sh`。

# 部署脚本

真正的部署脚本要处理旧应用的关闭，和新应用的启动。
正路来说，可以使用spring boot的优雅关闭，迟点再接上。野路子的方式是`kill -15`。这里要注意
- `kill -9`: 没有机会响应shutdownHook
- `kill -15`: 有机会响应shutdownHook

要先找到原来的旧应用才能kill
```bash
ps aux | grep java | grep medical | grep ${ENV} | awk '{ print $2 }
```
要留点时间给shutdownHook做清理，因此建议kill之后sleep一小段时间。
然后重新启动应用
```bash
nohup java -jar medical.jar --spring.profiles.active=${ENV} &
```

大功告成。