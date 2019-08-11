---
title: travis ci跳过触发构建
date: 2019-08-11 15:12:37
tags: [travis ci, devops, 技巧]
categories: [技巧]
keywords: [travis跳过构建, TRAVIS_COMMIT_MESSAGE, travis skip building]
description: travis跳过构建，可以在脚本使用TRAVIS_COMMIT_MESSAGE变量判断；或者以[skip \<keyword\>]形式提交commit message
---

# 问题背景

自从博客使用travis ci做构建和部署之后，更新博客非常方便。不过带来一个问题，那就是每次提交都触发了构建，但是有的提交并不是我想触发更新：
- 因为要切换电脑使用，本地内容提交到github
- 或者想`hexo new draft`，暂时保存为草稿，这也不需要触发travis ci构建
- 只是改很小的地方，没必要触发构建，在以后一起部署就好，不浪费公共资源

# 解决

解决问题的思路是，通过在构建之前检查git commit message，自己写脚本判断是否继续构建。或者travis ci自己可以自动识别特定git commit message，不做构建。

## TRAVIS_COMMIT_MESSAGE

如果要手动判断git commit message，首先要找到这个消息。查阅[官网资料](https://docs.travis-ci.com/user/environment-variables/#Default-Environment-Variables)，travis ci提供了内置的环境变量支持
>TRAVIS_COMMIT_MESSAGE: The commit subject and body, unwrapped.

自定义的检查脚本大概是
```bash
if [[ $TRAVIS_COMMIT_MESSAGE != "skip" ]]; then hexo clean && hexo g && hexo d ; fi ;
```

## [skip \<keyword\>]


事实上跳过构建是一个很通用的需求，travis ci提供了内置支持。参见 [Skipping-a-build](https://docs.travis-ci.com/user/customizing-the-build/#Skipping-a-build)
>The command should be one of the following forms:
>[<KEYWORD> skip]
>or
>[skip <KEYWORD>]
>where <KEYWORD> is either ci, travis, travis ci, travis-ci, or travisci. For example,
>[skip travis] Update README

只要git commit message是以`[skip <KEYWORD>]`形式开头，travis可以自动跳过构建。


