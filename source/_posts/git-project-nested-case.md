---
title: git仓库嵌套问题
date: 2019-12-03 19:35:31
tags: [git]
categories: [git]
keywords: [git nested, git submodule]
description: git项目嵌套，默认情况下会导致被嵌套的项目不能被外层项目识别。解决方法：1. 删除内层.git目录；2. git submodule add 添加子项目。
---

新建了一个项目，把github上一个网易云音乐的小程序和后台clone过来做定制。
但是git add后添加不上，文件不能提交上去。
<!-- more -->
```
C:\workspace\music_miniapp (master -> origin)
λ git add .

C:\workspace\music_miniapp (master -> origin)
λ git commit -m "repush"
On branch master
Your branch is up to date with 'origin/master'.

Changes not staged for commit:
        modified:   NeteaseMusicWxMiniApp (modified content, untracked content)
        modified:   netmusic-node (modified content, untracked content)

no changes added to commit
```

因为这2个子项目是从git上clone过来，有`.git`目录。Git 仓库嵌套后，被嵌套的 Git 仓库不能被外层 Git 仓库检测到。
于是删除两个子项目的`.git`目录，更新cached。
```
C:\workspace\music_miniapp (master -> origin)
λ git rm -rf --cached .
rm 'NeteaseMusicWxMiniApp'
rm 'README.md'
rm 'netmusic-node'
```

再次git add和commit，可以正常识别文件了。

删除子项目的`.git`目录，就不能正常pull从而更新。如果要保持嵌套项目更新，可以使用`git submodule `。
```
git submodule add https://github.com/sqaiyan/NeteaseMusicWxMiniApp
```