---
title: "Docker 容器内运行进程时文件系统权限的问题"
date: 2024-01-23T10:32:43+08:00
tags: ["docker", "linux"]
categories: ["docker", "linux"]
description: puid、pgid 解决容器内运行进程时文件系统权限的问题
---

# 容器内运行进程时文件系统权限的问题

**在 Docker 容器内，容器的文件系统通常是从主机复制而来的，但主机和容器可能有不同的用户和组标识。这就可能导致在容器内运行的进程对文件系统的访问权限出现问题**，例如写入文件时可能会因为权限不足而失败。

**PUID 和 PGID 的目的就是通过将容器内的进程映射到特定的用户和组，从而解决文件系统权限的问题**。通过设置这两个值，你可以确保容器内的进程以特定的用户和组的身份运行，使其在文件系统上具有足够的权限，从而避免权限问题。

一些常见的使用场景包括：
- 共享数据卷： 当你在容器内使用共享的数据卷时，确保容器内的进程具有正确的用户和组标识，以便能够正确地读写数据。
- 权限管理： 在容器内运行的服务或应用程序可能需要在主机上创建或修改文件，为了确保这些操作的正确性，需要设置正确的 PUID 和 PGID。


```bash
docker run -e PUID=1000 -e PGID=1000 myimage
```


查看当前用户的uid、gid信息
```bash
# id
uid=0(root) gid=0(root) groups=0(root)
```


# `docker run --user` 方式

Docker 的 `--user` 选项用于指定在容器内运行的进程的用户和/或组标识。通过设置 `--user`，你可以限制容器内进程的权限，以确保其以指定的用户或组的身份运行。

```bash
docker run --user <username or UID[:group or GID]> ...


# 指定用户名和组名
docker run --user myuser:mygroup myimage

# 指定用户名和组ID
docker run --user 1000:1000 myimage

# 只指定用户名，不指定组
docker run --user myuser myimage

# 只指定用户ID，不指定组
docker run --user 1000 myimage

```

# 两种方式对比


- 使用 `docker --user` 是直接在 docker run 命令中指定用户和组，是 **Docker 的原生选项**。
- 使用 `-e PUID` 和 `-e PGID` 是通过**环境变量**的方式传递用户和组的信息给容器内的进程，允许更灵活的配置。这种方式适用于**在运行时动态调整**用户和组。


# 扩展：Linux 的 uid 和 gid

（以下来自chatgpt）

在Linux系统中，UID（User Identifier）和GID（Group Identifier）是用于标识用户和用户组的数字标识符。每个用户和用户组都与一个唯一的数字相关联，这些数字就是UID和GID。

1. **UID（User Identifier）：**
   - UID是用于标识用户的数字。每个用户都有一个唯一的UID。
   - 在Linux系统中，UID的范围通常是从0到65535，其中0是保留给超级用户（root）的UID。
   - UID为0的用户是系统的超级用户，拥有对系统的完全访问权限。其他用户的UID是分配给普通用户的。

2. **GID（Group Identifier）：**
   - GID是用于标识用户组的数字。每个用户组都有一个唯一的GID。
   - 在Linux系统中，GID的范围通常也是从0到65535，其中0是保留给超级用户组的GID。
   - 用户属于一个主组（primary group），并且可以属于多个附加组（additional groups）。主组的GID是用户的基本组，而附加组是用户可能属于的其他组。

3. **/etc/passwd 文件：**
   - 用户的基本信息，包括用户名、UID、GID等，保存在/etc/passwd文件中。
   - 该文件的每一行对应一个用户的信息，字段之间使用冒号分隔。

4. **/etc/group 文件：**
   - 用户组的信息保存在/etc/group文件中，包括组名、GID以及组内的成员。
   - 该文件的每一行对应一个用户组的信息，字段之间同样使用冒号分隔。

5. **id 命令：**
   - 通过`id`命令可以查看当前用户的UID、GID以及所属的附加组。

示例：
```bash
$ id
uid=1000(username) gid=1000(username) groups=1000(username),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),116(lxd),130(lpadmin),131(sambashare)
```

上述输出表示当前用户的UID是1000，主组GID是1000，同时还属于其他一些附加组。

```bash
root@GreenCloud:~# cat /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
```

# 扩展： `/usr/sbin/nologin`

在系统中，通常在 `/etc/passwd` 文件中的用户条目中指定用户的登录 shell。如果某个用户的登录 shell 被设置为 `/usr/sbin/nologin`，则该用户将无法通过常规的登录方式进入系统。


/usr/sbin/nologin 是一个特殊的 shell，通常用于禁止用户登录系统。当系统管理员希望阻止某个用户通过登录（例如 SSH 或本地登录）方式进入系统，但仍然希望保留该用户的账户，可以将其登录 shell 设置为 /usr/sbin/nologin。

这个 nologin shell 并不提供一个交互式的命令行界面，而是在用户尝试登录时提供一条消息，并随即终止登录过程。

>This account is currently not available.

或者

>User account has expired


# 参考

- [Understanding PUID and PGID](https://docs.linuxserver.io/general/understanding-puid-and-pgid)
- chatgpt的相关提问
