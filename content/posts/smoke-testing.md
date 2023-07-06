---
title: 冒烟测试
date: 2019-07-22 18:04:21
tags: [测试, 微服务]
categories: [测试]
keywords: [冒烟测试, smoke testing, Build Verification Testing, BVT]
description: 冒烟测试，又叫Build Verification Testing。由开发执行，主要对核心路径、变更内容、修复bug进行测试。冒烟测试通过后，由测试人员进行下阶段的测试。
---

事情的起因是，帮朋友面试一个技术主管候选人。其中问了团队输出质量管理怎么搞，问了“冒烟测试”，对方一脸懵逼，似乎没有听过，甚至还想用压力测试来糊弄过去（压力大了就会冒烟嘛🙃）……
于是就就聊聊“冒烟测试”。
<!-- more -->
# 概念

以下定义引用自[Smoke Testing](http://softwaretestingfundamentals.com/smoke-testing/)
>SMOKE TESTING, also known as “Build Verification Testing”, is a type of software testing that comprises of a non-exhaustive set of tests that aim at ensuring that the most important functions work. The result of this testing is used to decide if a build is stable enough to proceed with further testing.

定义很简洁。几个关键点是：
- 构建后就应该执行
- 不是全量的测试集合
- 关注的是最重要的功能
- 冒烟测试的结果决定要不要继续下一阶段的测试

# 执行时机和覆盖内容

smoke test又叫Build Verification Testing（BVT）。顾名思义，是构建后就应该执行。验证一个构建，至少包含：
- 是否编译通过
- 核心功能有无受影响
- bug fix内容是否生效
- 此次修改内容是否生效
- 为了节省时间，通常考虑覆盖正常路径操作即可

从上面也可以看到，冒烟测试并不是一个全量测试，不会覆盖到所有细节。强调的是快速验证核心路径是否正常。如果核心路径都由问题，那么就没有必要进行下一阶段的测试。

# 测试用例

可以由测试和开发一起设计整理。
因为每次冒烟测试都会涉及到核心路径，可以把主路径相关的测试做成自动化测试，提高效率。

# 谁来执行

一个误区是冒烟测试交由测试人员进行。实际上应该由开发人员负责。开发人员对构建进行核心、简单的测试，一旦发现错误，就立即修复。由开发人员负责，一是对自己的产出负责，二是提高效率，减少沟通、文书的开销，这样才能快速验证。

# 价值

冒烟测试的价值在于尽快发现artifact的问题。尤其是低级的、阻塞核心功能的问题。
当然对于维护测试和开发的关系也是大有益处。试想提交给测试，结果根本运行不了、修复的bug根本不起作用，这么低级的问题都不解决就让他们干活，换谁都有意见啦。

