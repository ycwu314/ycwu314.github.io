---
title: linux signal 笔记
date: 2019-10-08 20:55:39
tags: [linux]
categories: [linux]
keywords: [sigkill sigterm]
description: sigterm可以捕捉、可以忽略，通常作为优雅关闭的方式。sigkill不可以捕捉、不可以忽略，是杀死进程的最后方式。
---

几个容易混淆的信号。
<!-- more -->

# sigkill

>The SIGKILL signal is sent to a process to cause it to terminate immediately (kill). In contrast to SIGTERM and SIGINT, this signal cannot be caught or ignored, and the receiving process cannot perform any clean-up upon receiving this signal. 

信号不可以被捕捉、不可以被忽略（init进程除外）。
应该把sigkill作为杀死进程的最后方式。（`kill -9`）

# sigterm

>The SIGTERM signal is sent to a process to request its termination. Unlike the SIGKILL signal, it can be caught and interpreted or ignored by the process. This allows the process to perform nice termination releasing resources and saving state if appropriate. SIGINT is nearly identical to SIGTERM.

信号可以被进程捕捉、忽略。
sigterm可以实现进程的优雅关闭。（`kill -15`）
类似sigint，但是不限于终端程序。

# sigint

>The SIGINT signal is sent to a process by its controlling terminal when a user wishes to interrupt the process. This is typically initiated by pressing Ctrl+C, but on some systems, the "delete" character or "break" key can be used

在终端里需要中断程序，使用ctrl + c 触发。

# sigquit

>The SIGQUIT signal is sent to a process by its controlling terminal when the user requests that the process quit and perform a core dump.

在终端触发，会core dump。

# sighup

>The SIGHUP signal is sent to a process when its controlling terminal is closed. It was originally designed to notify the process of a serial line drop (a hangup). In modern systems, this signal usually means that the controlling pseudo or virtual terminal has been closed.[4] Many daemons will reload their configuration files and reopen their logfiles instead of exiting when receiving this signal.[5] nohup is a command to make a command ignore the signal.

用于通知进程，终端已经关闭。
通常是在终端的控制进程结束时, 通知同一session内的各个作业, 这时它们与控制终端不再关联。
nohup命令可以让进程忽略sighup信号。


# 参考

- [Signal (IPC)](https://en.wikipedia.org/wiki/Signal_(IPC))