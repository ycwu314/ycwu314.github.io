---
title: "win10家庭版设置本地账号密码永不过期"
date: 2023-09-07T14:12:20+08:00
tags: [windows]
categories: [windows]
---

工作机器自带win10家庭版，使用本地账号，每隔一段时间提示要修改密码。修改密码后，又要修改自动登录密码，否则自动开机登录失败。
于是改成永不过期策略。

前提：
- win10 home版。专业版、旗舰版可以使用组策略修改。
- 本地创建的账号，非microsoft account。

1. 以管理员身份打开cmd

```
>net accounts
强制用户在时间到期之后多久必须注销?:     从不
密码最短使用期限(天):                    0
密码最长使用期限(天):                    42
密码长度最小值:                          0
保持的密码历史记录长度:                  None
锁定阈值:                                从不
锁定持续时间(分):                        30
锁定观测窗口(分):                        30
计算机角色:                              WORKSTATION
命令成功完成。
```

“密码最长使用期限”默认为42天。

2. 设置密码永不过期

```
wmic useraccount where "Name='xxx'" set PasswordExpires=false
```

3. 查看修改后的用户设置

```
net user xxx
```