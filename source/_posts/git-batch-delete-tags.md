---
title: 批量删除git标签
date: 2020-07-20 19:24:20
tags: [git, 技巧]
categories: [git]
keywords: [git tag delete]
description: 批量删除git标签。
---

很长时间没有搞过之前一个项目，拉下来发现很多自动化构建的标签。
<!-- more -->
```
C:\workspace\medical (master -> origin)
λ git pull origin
From code.aliyun.com:xxxxxx/medical
 * [new tag]         tags/20190804115002698_medical -> tags/20190804115002698_medical
 * [new tag]         tags/20190820225718365_medical -> tags/20190820225718365_medical
 * [new tag]         tags/20190822224002996_medical -> tags/20190822224002996_medical
// 省略一大堆
```

尼玛，太多了，而且都没用了，于是清理一下。

# 删除远程标签

```
C:\workspace\medical (master -> origin)
λ git show-ref --tag
d258885654a97e3f8816135f9e53394f2eaa30c3 refs/tags/tags/20190804115002698_medical
29254f6b0452de31db7d15fa942cb8d095d9dd80 refs/tags/tags/20190820225718365_medical

C:\workspace\medical (master -> origin)
λ git show-ref --tag | awk '{print ":"$2}' | xargs git push origin
To code.aliyun.com:xxxxxx/medical.git
 - [deleted]         tags/20190804115002698_medical
 - [deleted]         tags/20190820225718365_medical
 - [deleted]         tags/20190822224002996_medical
 - [deleted]         tags/20190829001121412_medical
```
在tag名前添加`:`，标记为删除

# 删除本地标签

```
git tag -l | xargs git tag -d
```
