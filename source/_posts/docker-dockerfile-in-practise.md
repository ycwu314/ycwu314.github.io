---
title: dockerfile使用经验
date: 2020-05-09 10:31:00
tags: [docker]
categories: [docker]
keywords: [docker env]
description:
---
{% asset_img slug [title] %}
<!-- more -->

# docker build 命令

在Dockerfile所在目录
```bash
# -t            Name and optionally a tag in the 'name:tag' format
# -f            Name of the Dockerfile (Default is 'PATH/Dockerfile')
# --force-rm    Always remove intermediate containers
# --no-cache    Do not use cache when building the image (很慢)

docker build -t ycwu/ycwu-alpine:v1 .
```
最后的`.`表示使用当前目录作为工作目录，ADD、COPY等命令以此作为操作的上下文。
如果文件名不是Dockerfile，要`-f`指定。

```bash
$ docker build --no-cache=true -f /path/to/Dockerfile -t some_tag -t image_name:image_version /path/to/build
```

# ENV

通过ENV定义的环境变量，可以在dockerfile被后面的所有指令中使用。
```Dockerfile
ENV TZ=Asia/Shanghai
# 使用等号，可以在一个ENV指定设置多个环境变量
ENV a=1 b=2            
ENV c 3
```
ENV的内容会写入层。但是经过测试，非等号语法方式设置环境变量，偶尔不能正确持久化到层，有些奇怪。

在`docker run`命令中通过`-e`标记来传递环境变量，这样容器运行时就可以使用该变量。
```
docker run --env <key>=<value>
```

如果只需要对一条指令设置环境变量，可以使用这种方式：`RUN <key>=<value> <command>`。

# WORKDIR

指定工作目录。如果不存在，则自动创建。

# 复制文件

对于 COPY 和 ADD 命令来说，如果要把本地的文件拷贝到镜像中，那么本地的文件必须是在上下文目录中的文件。因为在执行 build 命令时，docker 客户端会把上下文中的所有文件发送给 docker daemon。

**COPY和ADD都只复制目录中的内容而不包含目录自身**。

举个例子，Dockerfile所在上下文目录情况：
```
[root@host143 tmp]# ls -al
总用量 4
drwxr-xr-x  3 root root  36 5月   9 11:30 .
drwxr-xr-x. 7 root root 138 5月   9 11:27 ..
-rw-r--r--  1 root root  80 5月   9 11:33 Dockerfile
drwxr-xr-x  2 root root  32 5月   9 11:28 haha
[root@host143 tmp]# ls -al haha
总用量 8
drwxr-xr-x 2 root root 32 5月   9 11:28 .
drwxr-xr-x 3 root root 36 5月   9 11:30 ..
-rw-r--r-- 1 root root  5 5月   9 11:28 1.txt
-rw-r--r-- 1 root root  8 5月   9 11:28 2.txt
```

执行如下的构建
```Dockerfile
FROM alpine:3.11.6
MAINTAINER ycwu

WORKDIR /data
# 把haha目录下内容复制到/data下面，不包括haha目录本身
ADD haha .

ENTRYPOINT ["sh"]
```

进去容器看看，没有haha目录。
```
/data # ls -al
total 8
drwxr-xr-x    1 root     root            32 May  9 03:33 .
drwxr-xr-x    1 root     root            18 May  9 03:33 ..
-rw-r--r--    1 root     root             5 May  9 03:28 1.txt
-rw-r--r--    1 root     root             8 May  9 03:28 2.txt
```

如果要保留目录名，只需要在`<dest>`加上目录名：
```Dockerfile
ADD haha ./haha
```
进入容器看看：
```
/data # ls
haha
/data # ls haha
1.txt  2.txt
```

## ADD

```Dockerfile
ADD <src>... <dest>
```

必须是在上下文目录和子目录中，无法添加`../a.txt`这样的文件。如果`<src>`是个目录，则复制的是目录下的所有内容，但不包括该目录。
`<dest>`可以是绝对路径，也可以是相对WORKDIR目录的相对路径。

ADD命令支持下载远程文件，但是官方例子建议使用`RUN curl`或者`RUN wget`替代，因为可以直接删除源文件。

>Because image size matters, using ADD to fetch packages from remote URLs is strongly discouraged; you should use curl or wget instead. That way you can delete the files you no longer need after they’ve been extracted and you don’t have to add another layer in your image. For example, you should avoid doing things like:

```Dockerfile
ADD http://example.com/big.tar.xz /usr/src/things/
RUN tar -xJf /usr/src/things/big.tar.xz -C /usr/src/things
RUN make -C /usr/src/things all
```

And instead, do something like:
```Dockerfile
RUN mkdir -p /usr/src/things \
    && curl -SL http://example.com/big.tar.xz \
    | tar -xJC /usr/src/things \
    && make -C /usr/src/things all
```

ADD支持自动解压缩文件，比如tar。

## COPY

COPY最重要的功能是multi-stage build中复制产物。

## 技巧

如果要把多个文件复制到容器，其中有不经常变更、经常变更的文件，那么应该分开写，加速镜像构建。

假设a.txt（不经常变更）、b.txt（经常变更）、c.txt（经常变更）。
```Dockerfile
# a.txt 不经常变更，单独占一层，大概率可以重用缓存。
ADD a.txt .
ADD b.txt c.txt .
```


# ENTRYPOINT

指定镜像的执行程序，只有最后一条ENTRYPOINT指令有效。

# CMD

# 参考

- [深入Dockerfile（一）: 语法指南](https://github.com/qianlei90/Blog/issues/35)
- [Dockerfile 中的 COPY 与 ADD 命令](https://www.cnblogs.com/sparkdev/p/9573248.html)
- [Best practices for writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices)

