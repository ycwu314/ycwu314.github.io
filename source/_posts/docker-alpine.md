---
title: 使用alpine基础镜像
date: 2020-05-07 18:12:23
tags: [docker, linux]
categories: [docker]
keywords: [alpine docker, glibc vs musl libc]
description: 记录使用alpine基础镜像的经验。
---

最近使用alpine制作镜像，记录使用经验。
<!-- more -->

>Alpine Linux is a Linux distribution built around musl libc and BusyBox. The image is only 5 MB in size.

# glibc vs musl libc

1. glibc是linux下面c标准库的实现，即GNU C Library。glibc本身是GNU旗下的C标准库，后来逐渐成为了Linux的标准c库。其实现了常见的C库的函数，支持很多种系统平台，功能很全，但是也相对比较臃肿和庞大。

2. Musl是一个轻量级的C标准库，主要目标是跨平台，减少底层依赖，比如移植到新的os，支持嵌入式操作系统和移动设备。

3. uClibc 一个小型的C语言标准库，主要用于嵌入式。和glibc在源码结构和二进制上，都不兼容。

4. Eglibc = Embedded GLIBC 。glibc的原创作组织FSF推出的glibc的一种变体，目的在于将glibc用于嵌入式系统。保持源码和二进制级别的兼容于Glibc 源代码架构和ABI层面兼容。之前用glibc编译的程序，可以直接用eglibc替换，而不需要重新编译。 这样就可以复用之前的很多的程序了。 Eglibc的最主要特点就是可配置，这样对于嵌入式系统中，你所不需要的模块，比如NIS，locale等，就可以裁剪掉，不把其编译到库中，使得降低生成的库的大小了。

alpine和centos的重要差别是：libc从glibc换成了musl。因此很多软件包不能直接使用。

为了能够正常使用这些基于glibc的软件，可以使用[alpine-pkg-glibc](https://github.com/sgerrand/alpine-pkg-glibc)：
```bash
# -q: 安静模式，不显示进度条
# -O: 保存到文件
wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub
wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.31-r0/glibc-2.31-r0.apk
adk add glibc-2.31-r0.apk
```

# 包管理工具： apk

alpine使用apk作为包管理工具，功能对应yum、apt。

# 时区

alpine默认把时区相关部分也去掉了。需要安装tzdata。
```
ENV TZ=Asia/Shanghai
RUN apk add -U tzdata \ 
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \ 
    && echo '$TZ' > /etc/timezone
```

# 国际化支持

i18n支持也是被删掉的。

>If you are using tools like `localedef` you will need the `glibc-bin` and `glibc-i18n` packages in addition to the glibc package.

```bash
wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.31-r0/glibc-bin-2.31-r0.apk
wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.31-r0/glibc-i18n-2.31-r0.apk
apk add glibc-bin-2.31-r0.apk glibc-i18n-2.31-r0.apk
/usr/glibc-compat/bin/localedef -i en_US -f UTF-8 en_US.UTF-8
rm -f glibc-bin-2.31-r0.apk glibc-i18n-2.31-r0.apk
```

# 安装JDK

Java是基于GUN Standard C library(glibc)。
apk支持安装openjdk、openjre。

```Dockerfile
FROM amd64/alpine:3.11.6 
MAINTAINER ycwu

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV TZ=Asia/Shanghai
ENV JAVA_HOME=/usr/lib/jvm/default-jvm
ENV PATH=${PATH}:${JAVA_HOME}/bin:/usr/glibc-compat/bin

# change apk source mirrors
RUN echo http://mirrors.ustc.edu.cn/alpine/v3.11/main > /etc/apk/repositories && \
    echo http://mirrors.ustc.edu.cn/alpine/v3.11/community >> /etc/apk/repositories && \
    apk update && apk upgrade

# install glibc
RUN wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub \
    && wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.31-r0/glibc-2.31-r0.apk \
    && apk add glibc-2.31-r0.apk && rm -rf glibc-2.31-r0.apk

# install i18n
RUN wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.31-r0/glibc-bin-2.31-r0.apk \
    && wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.31-r0/glibc-i18n-2.31-r0.apk \
    && apk add glibc-bin-2.31-r0.apk glibc-i18n-2.31-r0.apk \
    && /usr/glibc-compat/bin/localedef -i en_US -f UTF-8 en_US.UTF-8 \ 
    && rm -rf glibc-bin-2.31-r0.apk glibc-i18n-2.31-r0.apk 

# setup localtime & timezone
RUN apk add -U tzdata \ 
    && echo '$TZ' > /etc/timezone \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime 

# install openjdk8
RUN apk add openjdk8

# other tools
RUN apk add tcpdump

ENTRYPOINT ["sh"]
```

```
docker build -t ycwu/ycwu-alpine:v1 .
```
镜像大小165MB。

注意：
- alpine容器中通过env或者printenv查看环境变量


这里还有压缩空间，优化i18n和locale：只保留utf8和asia/shanghai。
```
/ # /usr/glibc-compat/bin/localedef --usage

System's directory for character maps : /usr/glibc-compat/share/i18n/charmaps
		       repertoire maps: /usr/glibc-compat/share/i18n/repertoiremaps
		       locale path    :
/usr/glibc-compat/lib/locale:/usr/glibc-compat/share/i18n
```

```
RUN apk add -U tzdata \ 
    && cp /usr/share/zoneinfo/Asia/Shanghai tz &&  rm -rf /usr/share/zoneinfo && mkdir -p /usr/share/zoneinfo/Asia && cp tz /usr/share/zoneinfo/Asia/Shanghai && rm -f tz \ 
    && echo '$TZ' > /etc/timezone \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime 
```
还有更加直接粗暴的做法：把文件ADD进去。


