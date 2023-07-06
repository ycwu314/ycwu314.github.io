---
title: qemu显示设备和能力
date: 2022-04-26 10:06:49
tags: [qemu]
categories: [qemu]
keywords: [qemu, 虚拟显卡]
description: 整理的qemu虚拟显卡设备类型和能力。
---

# 设备概念和对比

qemu支持的虚拟显卡设备类型比较多。初次接触会比较懵逼。
直到阅读大佬kraxel的文章，受益良多:
[VGA and other display devices in qemu](https://www.kraxel.org/blog/2019/09/display-devices-in-qemu/)

<!-- more -->

根据文章整理成表格对比：

|                       | VGA compatible | vgabios support | UEFI support | linux driver  | PCI Express slot | Remarks                                                                                                                               |
|-----------------------|----------------|-----------------|--------------|---------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| standard VGA          | √              | √               | √            | √             | ×                |                                                                                                                                       |
| bochs                 | ×              | √               | √            | √             | √                |                                                                                                                                       |
| virtio vga            | √              | √               | √            | √             | ×                |                                                                                                                                       |
| virtio gpu            | ×              | ×               | √            | √             | √                |                                                                                                                                       |
| vhost-user virtio gpu |                |                 |              |               |                  | There is a vhost-user variant for both virtio vga and virtio gpu. This allows to run the virtio-gpu emulation in a separate process.  |
| qxl vga               | √              | √               | √            | √             | ×                |                                                                                                                                       |
| qxl                   | ×              | ×               | √            | √             | ×                | Providing multihead support for windows guests is pretty much the only use case for this device.                                     |
| cirrus vga            | √              | √               | √            | √             | ×                | Emulates a Cirrus SVGA device which used to be modern in the 90ies of the last century                                                |
| ramfb                 | ×              | √               | √            | √             | ×                |                                                                                                                                       |


一些概念：
- VGA compatibility：即使guest不安装驱动，也能支持vga相关能力，但是性能不好。
- VGA 文本模式：没多大卵用了。
- 2D加速：没多大卵用了。
- spice + qxl 实现客户端2D加速：没多大卵用了。
- vhost-user virtio gpu：使用单独进程进行模拟virtio gpu。安全性更好。且opengl性能也好一些。
- qxl和qxl vga： 差别在于VGA compatibility。qxl （primary='no'）通常支持windows的多屏输出。
- cirrus vga：兼容90年代系统
- ramfb：通常用于boot阶段的显示输出，直到os加载vgpu驱动后。

# 使用建议

作者在文章末尾给出了使用建议。

For the desktop use case (assuming display performance matters and/or you need multihead support), in order of preference:
- virtio vga or virtio gpu, if your guest has drivers
- qxl vga, if your guest has drivers
- bochs display device, when using UEFI
- standard VGA

For the server use case (assuming the GUI is rarely used, or not at all), in order of preference:
- serial console, if you can work without a GUI
- bochs display device, when using UEFI
- standard VGA

On arm systems display devices with a pci memory bar do not work, which reduces the choices alot. We are left with:
- virtio gpu, if your guest has drivers
- ramfb

