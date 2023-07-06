---
title: dockerfile使用经验
date: 2020-05-09 10:31:00
tags: [docker]
categories: [docker]
keywords: [docker env]
description: 整理dockerfile编写经验
---

# docker build 命令

在Dockerfile所在目录
<!-- more -->
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


```Dockerfile
# change apk source mirrors
RUN echo http://mirrors.ustc.edu.cn/alpine/v3.11/main > /etc/apk/repositories && \
    echo http://mirrors.ustc.edu.cn/alpine/v3.11/community >> /etc/apk/repositories
RUN apk update && apk upgrade
```

# shell模式和exec模式

- Shell格式：`<instruction> <command>`。
- Exec格式：`<instruction> ["executable", "param1", "param2", ...]`。

exec模式的参数要使用双括号：
>The exec form is parsed as a JSON array, which means that you must use double-quotes (“) around words not single-quotes (‘).

## shell模式

使用 shell 模式时，docker 会以 `/bin/sh -c "task command"` 的方式执行任务命令。也就是说容器中的 1 号进程不是任务进程而是 bash 进程。
shell 模式可以解析变量。

## exec模式

使用 exec 模式时，容器中的任务进程就是容器内的 1 号进程。
（如果执行shell脚本，则依然是sh）

因为exec模式不启动shell，因此默认情况下缺少环境变量解析的能力。如果要解析环境变量，可以：
```Dockerfile
ENTRYPOINT ["/bin/bash", "-c", "echo", "$HOME"]
```



# ETNTRYPOINT & CMD


## ENTRYPOINT

指定镜像的执行程序，只有最后一条ENTRYPOINT指令有效。

如果想要覆盖ENTRYPOINT命令，需要在docker run -it [image]后面添加--entrypoint string参数

每个Dockerfile只能有一个ENTRYPOINT命令，如果存在多个ENTRYPOINT命令，则执行最后一个ENTRYPOINT。

## CMD

**CMD 指令允许用户指定容器的默认执行的命令。此命令会在容器启动且 docker run 没有指定其他命令时运行。**

每个Dockerfile只能有一个CMD命令，如果存在多个CMD命令，则执行最后一个CMD。


## 区别

ENTRYPOINT 中的参数始终会被使用。
CMD设置的命令能够被docker run命令后面的命令行参数替换。

# docker entryfile sh

一些软件提供提供的dockerfile，入口的`docker-entrypoint.sh`脚本值得看看。
以[mysql 5.7 docker-entrypoint.sh](https://raw.githubusercontent.com/docker-library/mysql/607b2a65aa76adf495730b9f7e6f28f146a9f95f/5.7/docker-entrypoint.sh)为例子。

```sh
set -eo pipefail
shopt -s nullglob

# if command starts with an option, prepend mysqld
if [ "${1:0:1}" = '-' ]; then
	set -- mysqld "$@"
fi
```

## set

- `set -e`: 后续脚本执行遇到非0返回值就退出。好处遇到执行错误就退出，避免往后产生更多错误。
```
Exit immediately if a pipeline (which may consist of a single simple command), a subshell 
command enclosed in parentheses, or one of the commands executed as part of a command list
enclosed by braces (see SHELL GRAMMAR above) exits with a non-zero status.
```

- `set -o pipefail`：管道模式的命令，遇到错误就退出执行。
```
If set, the return value of a pipeline is the value of the last (rightmost) command to exit with a non-zero status,or zero if all commands in the pipeline exit successfully. This option is disabled by default.
```

## shopt

shopt命令用于显示和设置shell中的行为选项。
`shopt -s nullglob`：如果 nullglob 选项被设置，并且没有找到任何匹配，这个单词被删除。

## `if [ "${1:0:1}" = '-' ];`

`${1:0:1}`是bash的语法。从第N个参数截取字符串。
第一个参数：命令行传入的第N个参数。
第二个参数：截取的开始索引。
第三个参数：截取的结束索引。

`${1:0:1}`是指从`$1`截取`0-1`的字符串。
整个if判断看是不是`-`开头的选项。

## `set -- mysqld "$@"`

`set --`会将他后面所有以空格区分的字符串, 按顺序分别存储`$1`，`$2`，... ，`$@`。
```
If no arguments follow this option, then the positional parameters are unset. Otherwise, the
positional parameters are set to the args, even if some of them begin with a -.
```

当 `$*` 和 `$@` 不被双引号`" "`包围时，它们之间没有任何区别，都是将接收到的每个参数看做一份数据，彼此之间以空格来分隔。
但是当它们被双引号`" "`包含时，就会有区别了：
- `"$*"`会将所有的参数从整体上看做一份数据，而不是把每个参数都看做一份数据。
- `$@"`仍然将每个参数都看作一份数据，彼此之间是独立的。

```bash
#! /bin/bash

echo "param: " $*

echo 'loop "$@"'
for x in "$@"
do
    echo $x
done

echo

echo 'loop "$*"'
for x in "$*"
do
    echo $x
done
```

```bash
[root@host143 ycwu]# ./t2.sh 123 456
param:  123 456
loop "$@"
123
456

loop "$*"
123 456
```

## exec

使用exec command方式，会用command进程替换当前shell进程，并且保持PID不变。执行完毕，直接退出，不回到之前的shell环境。

`exec "$@"`: 作为entrypoint的兜底，执行用户传入的命令。

# 参考

- [深入Dockerfile（一）: 语法指南](https://github.com/qianlei90/Blog/issues/35)
- [Dockerfile 中的 COPY 与 ADD 命令](https://www.cnblogs.com/sparkdev/p/9573248.html)
- [Best practices for writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices)
- [docker entrypoint入口文件详解](https://www.cnblogs.com/breezey/p/8812197.html)
- [分析Mysql 5.6的Dockerfile](https://www.cnblogs.com/ivictor/p/4832832.html)
- [【exec】shell脚本中的 exec 命令](https://www.jianshu.com/p/ca012415cd5f)