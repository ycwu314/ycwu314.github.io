---
title: python环境相关
date: 2019-09-20 11:35:11
tags: [python]
categories: [python]
keywords: [python site packages, python dist packages, pipenv]
description: 
---

# dist-packages vs site-packages


>dist-packages is a Debian-specific convention that is also present in its derivatives, like Ubuntu. Modules are installed to dist-packages when they come from the Debian package manager into this location

>dist-packages instead of site-packages. Third party Python software installed from Debian packages goes into dist-packages, not site-packages. This is to reduce conflict between the system Python, and any from-source Python build you might install manually.


Debian类操作系统的包管理器，会使用dist-packages保存安装的第三方库。
用户自己安装的python，第三方库默认会保存在site-packages。

<!-- more -->

# pipenv

pipenv支持pipfile，可以替代requirements.txt文件。
一个项目对应一个 Pipfile，支持开发环境与正式环境区分。默认提供 default 和 development 区分。
提供版本锁支持，存为 Pipfile.lock。
```
pip install pipenv
```
使用
```
$ cd project_folder
$ pipenv install requests
```
执行
```
pipenv run python main.py
```

# virtualenv

virtualenv用于创建独立的Python环境，多个Python相互独立，互不影响
安装
```
pip install virtualenv
```
创建
```
virtualenv [虚拟环境名称-也是目录名称] 
```
启动
```
cd ENV
source ./bin/activate
```
退出
```
deactivate
```

# virtualenvwrapper

Virtaulenvwrapper是virtualenv的扩展包：
- 将所有虚拟环境整合在一个目录下
- 快速切换虚拟环境

# 参考

- [Pipenv & Virtual Environments](https://docs.python-guide.org/dev/virtualenvs/)
- [Python新利器之pipenv](https://www.jianshu.com/p/00af447f0005)
- [Python三神器之virtualenv、virtualenvwrapper](https://www.jianshu.com/p/3abe52adfa2b)


