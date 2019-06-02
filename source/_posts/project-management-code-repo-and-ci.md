---
title: '代码仓库，CI，项目管理的调研'
date: 2019-06-01 21:50:43
tags: devops
categories: devops
---

# 背景

几个人业余折腾项目，要考虑代码托管，自动化构建，任务管理问题。

需求
- 免费私有仓库
- 项目管理，支持需求管理，关联任务，进度统计等
- 自动化构建和部署，从源码到云平台
- 尽量在一个平台搞定

约束
- 使用阿里云平台ecs等中间件

于是调研了国内常见的码云、coding、阿里云code等。

<!-- more -->
# 码云 oschina

good
- 支持阿里云codepipeline，自动构建和部署

bad
- 项目管理功能看上去一般
- 界面一般

# coding

good
- 界面好看
- 项目管理友好

bad
- 自动化构建和部署，不支持和阿里云集成（鹅厂旗下的。。。）。要自己搭建jenkin做ci。

# 阿里云code + 阿里云云效

[阿里云code](https://code.aliyun.com/) 是代码仓库。
[阿里云云效](https://cn.aliyun.com/product/yunxiao) 是项目管理，持续集成，持续交付平台。

good
- 支持阿里云构建（废话）
- 项目管理就是aone的商业版，用习惯了（ui毫无惊喜）
- 企业成员（研发、测试）小于30可申请扶持计划：审核通过可0元享一站式研发套餐。[云效收费](https://help.aliyun.com/document_detail/92574.html?spm=a2c4g.11186623.4.1.4f06ea50bk0qRa)


# 其他

GitHub是不考虑的。速度慢，还有众所周知的风险。
GitLab也是不考虑的。一是协作的人少，也没有到达足够的商业保密需要；二是GitLab以前用过挺消耗资源，减少不必要的机器成本和运维成本。

# 结论

阿里云code + 阿里云云效 符合我们的需求。（ps. @阿里云 可以加个鸡腿吗）



