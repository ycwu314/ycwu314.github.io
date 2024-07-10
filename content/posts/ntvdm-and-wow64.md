---
title: "Ntvdm and Wow64"
date: 2024-07-10T14:37:07+08:00
tags: [windows]
categories: [windows]
description: 
---

一篇有趣的文章：
[Restoring support for 16-bit applications in modern Windows versions](https://fabulous.systems/posts/2022/12/16-bit-support-in-64-bit-windows/)




# WoW64

WoW64（Windows 32-bit on Windows 64-bit）是Microsoft Windows操作系统的一个子系统，它提供在所有Windows 64位系统上运行32位应用程序的能力。

WOW64 模拟器以用户模式运行。 它在 32 位版本的 Ntdll.dll 和处理器内核之间提供一个接口，并拦截内核调用。

在技术上，WoW64主要使用三个动态链接库（DLL）实现：
- Wow64.dll，通往Windows NT内核的核心接口，它转换32位与64位调用，包括指针和调用栈操作。
- Wow64win.dll，为32位应用程序提供适当的入口点。
- Wow64cpu.dll，负责解决进程从32位切换到64位模式。

Wow64.dll 为 Ntoskrnl.exe 入口点函数提供核心仿真基础架构和基干。 
- Wow64Win.dll 为 Win32k.sys 入口点函数提供基干。
- （仅限 x64）Wow64Cpu.dll 为在 x64 上运行 x86 程序提供支持。 
- （仅限 Intel Itanium）IA32Exec.bin 包含 x86 软件仿真器。
- （仅限  Intel Itanium） Wowia32x.dll 提供 IA32Exec.bin 和 WOW64 之间的接口。 
- （仅限 ARM64） xtajit.dll 包含 x86 软件模拟器。 
- （仅限 ARM64） wowarmw.dll 支持在 ARM64 上运行 ARM32 程序。

环境变量也不同。

资料：
-[WOW64 Implementation Details](https://learn.microsoft.com/en-us/windows/win32/winprog64/wow64-implementation-details)


# NTVDM

NTVDM 或 NT 虚拟 DOS 机是 1993 年推出的一个系统组件，适用于所有 IA-32 版本的 Windows NT 系列（不包括 64 位版本的操作系统）。 该组件允许在 32 位 Windows 操作系统上执行 16 位 Windows 应用程序，以及执行 16 位和 32 位 DOS 应用程序。 作为单一 DOS（或 Windows 3.x）环境基础的 Windows NT 32 位用户模式可执行文件称为 ntvdm.exe。

NTVDM 子系统提供了一个运行环境，可复制在 MS-DOS 5.0 上运行的系统，包括所有必要的 BIOS 调用、Windows 3.1 内核和 Win16 API 本身。

为了执行 DOS 程序，NTVDM 加载 NTIO.SYS，NTIO.SYS 又加载 NTDOS.SYS，NTDOS.SYS 执行修改后的 COMMAND.COM，以运行作为命令行参数传递给 NTVDM 的应用程序。 16 位真实模式系统文件是其 MS-DOS 5.0 对应文件 IO.SYS、MSDOS.SYS 和 COMMAND.COM的精简派生版本，删除了对 FAT 文件系统的所有硬连接假设，并使用无效操作码 0xC4 0xC4 跳转到 32 位 NTVDM 处理请求。

Win64 系统都移除了ntvdm的支持。

资料：
- [NTVDM and 16-bit app support](https://learn.microsoft.com/en-us/windows/compatibility/ntvdm-and-16-bit-app-support)
- [Virtual DOS machine](https://en.wikipedia.org/wiki/Virtual_DOS_machine)



# cpu 运行模式

来自gemini整理。

## 实模式（Real mode）

实模式是x86 CPU最早的运行模式，也是最简单的模式。在实模式下，CPU只能访问16位地址，寻址范围为64KB。实模式没有任何内存保护机制，因此任何程序都可以访问任何内存地址，这可能会导致程序互相干扰甚至崩溃操作系统。

实模式主要用于运行旧的16位操作系统和应用程序，例如DOS和Windows 3.x。

## 保护模式（Protected mode）

保护模式是为了解决实模式的局限性而引入的。在保护模式下，CPU可以访问32位地址，寻址范围为4GB。保护模式引入了内存保护机制，可以将内存划分成多个段，每个段都有自己的访问权限。这可以防止程序互相干扰，提高系统的稳定性和安全性。

保护模式还引入了虚拟内存机制，可以将物理内存映射到虚拟地址空间中。这使得程序可以访问比实际物理内存更大的地址空间。

保护模式主要用于运行32位操作系统和应用程序，例如Windows XP和Linux。

## 长模式（Long mode）

长模式是为了进一步扩展CPU寻址能力和增强功能而引入的。在长模式下，CPU可以访问64位地址，寻址范围为16EB（约为16777216PB）。长模式还支持更大的物理内存地址空间，理论上可以支持多达128ZB的物理内存。

长模式还引入了新的指令集，例如SSE2、AVX和AVX2，可以提高浮点运算性能。

长模式主要用于运行64位操作系统和应用程序，例如Windows 10和Linux 64位版本。

其他：
- 长模式也被称为x86-64或AMD64。
- 并不是所有的x86 CPU都支持长模式。只有支持EM64T扩展指令集的CPU才能运行在长模式下。
- 在支持长模式的CPU上，默认情况下会启动长模式。但是，可以通过BIOS设置或操作系统配置切换到传统模式。


# cpu 运行模式和windows应用关系

长模式不支持 NTVDM 所需的 VM86 CPU 代码，以启用 16 位段寻址，因此必须在所有 x86_64 版本的 Windows 中删除。

当 CPU 在传统模式下运行时，可完全支持 32 位和 16 位应用程序。

在两种运行模式之间切换的唯一方法是硬重置 CPU 本身，这使得在不重启整个系统的情况下，两种运行模式无法无缝集成。 因为启动 64 位 Windows 系统将始终强制 CPU 在 Long 模式下运行，所以无法返回到允许在运行时执行 16 位应用程序的模式。 事实上，即使在 Long 模式下切换到 32 位兼容性模式（而不是传统模式），也需要额外的抽象层。 每次在 64 位 Windows 系统上启动 32 位应用程序时，操作系统都会调用 WoW64 子系统，该子系统作为兼容层，提供在 64 位系统上运行 32 位应用程序所需的接口。


