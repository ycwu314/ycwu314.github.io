---
title: "rclone 文档笔记"
date: 2023-12-21T17:30:31+08:00
tags: ["rclone"]
categories: ["self-hosted"]
description: rclone官方文档笔记
---

官方文档：

https://rclone.org/commands/rclone_mount


# windows系统

## 前置条件

需要先安装WinFsp，提供fuse支持。
>WinFsp is an open-source Windows File System Proxy which makes it easy to write user space file systems for Windows. It provides a FUSE emulation layer which rclone uses combination with cgofuse. 

## 不支持后台运行

win不支持`--daemon`参数。只能前台运行。

`--no-console`参数能够不显示前台输出。

## Mounting modes on windows

Windows系统区分固定驱动器（`fixed drive`）和网络驱动器(`network drive`)。

### fixed disk drive

When mounting as a fixed disk drive you can either mount to an unused drive letter, or to a path representing a nonexistent subdirectory of an existing parent directory or drive. 

Using the special value `*` will tell rclone to automatically assign the next available drive letter, starting with Z: and moving backward. Examples:

```
rclone mount remote:path/to/files *
rclone mount remote:path/to/files X:
rclone mount remote:path/to/files C:\path\parent\mount
rclone mount remote:path/to/files X:
```

### network drive

To mount as network drive, you can add option --network-mode to your mount command. Mounting to a directory path is not supported in this mode, it is a limitation Windows imposes on junctions, so the remote must always be mounted to a drive letter.
```
rclone mount remote:path/to/files X: --network-mode
```


If you specify a full network share UNC path with --volname, this will implicitly set the --network-mode option, so the following two examples have same result:
```
rclone mount remote:path/to/files X: --network-mode
rclone mount remote:path/to/files X: --volname \\server\share
```

### 扩展

Windows的UNC（Universal Naming Convention）路径是一种用于标识网络资源的路径格式。UNC路径用于访问网络上的共享文件夹或打印机等资源。

UNC路径的格式如下：

```
\\<计算机名称>\<共享资源>
```


## 文件系统权限

默认是`--file-perms 0666 --dir-perms 0777`。即所有人都可以访问，但不可以执行。

如果要写入文件，通常要配置`VFS File Caching`。

posix的ACL和windows的有细微区别。目前没碰到，先不研究。

## Administrator 

Administrator 账号创建的`驱动器`，不能被其他人访问，即使是提权成为Administrator （UAC）。

Administrator 映射的目录，则不受此限制。

# NFS

目前没碰到，先不研究。

# rclone mount vs rclone sync/copy

mount不能retry。 sync / copy 会retry。

原因是mount要保持文件系统的一致性。

# `--attr-timeout`

重要的一节！

为什么要缓存目录属性：

>You can use the flag --attr-timeout to set the time the kernel caches the attributes (size, modification time, etc.) for directory entries.
>
>The default is 1s which caches files just long enough to avoid too many callbacks to rclone from the kernel.


不缓存目录的场景，以及带来的问题：

>In theory 0s should be the correct value for filesystems which can change outside the control of the kernel. 
>
>However this causes quite a few problems such as rclone using too much memory, rclone not serving files to samba and excessive time listing directories.
>
>If you set it higher (10s or 1m say) then the kernel will call back to rclone less often making it more efficient, however there is more chance of the corruption issue above.


# VFS - Virtual File System

为什么需要VFS：提供文件的随机访问、追加写入等能力。

>Cloud storage objects have lots of properties which aren't like disk files - you can't extend them or write to the middle of them, so the VFS layer has to deal with that.
>
>The VFS layer also implements a directory cache - this caches info about files and directories (but not the data) in memory.


## VFS Directory Cache

```
--dir-cache-time duration   Time to cache directory entries for (default 5m0s)
--poll-interval duration    Time to wait between polling for changes. Must be smaller than dir-cache-time. Only on supported remotes. Set to 0 to disable (default 1m0s)
```

在`--dir-cache-time`时间内：
- vfs认为目录是最新的，不需要从后端刷新
- 通过vfs更新，则会立即失效cache
- 远程cloud storage更新了对应目录，则vfs无法感知！

手动刷新目录缓存的几种方式：

```
# invalidate full cache
kill -SIGHUP $(pidof rclone)

# invalidate full cache
rclone rc vfs/forget

# Or individual files or directories:
rclone rc vfs/forget file=path/to/file dir=path/to/dir

```


# VFS File Buffering

`--buffer-size` 单个打开文件的内存中的缓存上限。

rclone使用的最大缓存上限：`--buffer-size * open files`


# VFS File Caching


缓存文件到本地。

在一些场景需要关闭，比如同时读取和写入到同一个文件。

```
--cache-dir string                     Directory rclone will use for caching.
--vfs-cache-mode CacheMode             Cache mode off|minimal|writes|full (default off)
--vfs-cache-max-age duration           Max time since last access of objects in the cache (default 1h0m0s)
--vfs-cache-max-size SizeSuffix        Max total size of objects in the cache (default off)
--vfs-cache-min-free-space SizeSuffix  Target minimum free space on the disk containing the cache (default off)
--vfs-cache-poll-interval duration     Interval to poll the cache for stale objects (default 1m0s)
--vfs-write-back duration              Time to writeback files after last use when using cache (default 5s)
```

当关闭`vfs-cache-mode`且同时运行两个相同rclone挂载路径的case：
>You should not run two copies of rclone using the same VFS cache with the same or overlapping remotes if using --vfs-cache-mode > off. 
>
>This can potentially cause data corruption if you do. 
>
>You can work around this by giving each rclone its own cache hierarchy with --cache-dir. 
>
>You don't need to worry about this if the remotes in use don't overlap.


## `--vfs-cache-mode` 对比

使用bard整理这几种模式的差异：

| Feature                       | off       | minimal   | writes    | full      |
|--------------------------------|------------|-----------|-----------|-----------|
| Disk caching for reads        | No        | No        | No        | Yes       |
| Disk caching for writes       | No        | Yes       | Yes       | Yes       |
| Supports opening files for both read and write | No        | No        | Yes       | Yes       |
| Supports seeking in files opened for write   | No        | No        | Yes       | Yes       |
| Supports O_APPEND and O_TRUNC open modes      | No        | No        | Yes       | Yes       |
| Retries failed uploads                       | No        | No        | Yes       | Yes       |
| Sparse files                                 | No        | No        | No        | Yes       |
| Buffers reads ahead to disk                   | No        | No        | No        | Yes       |
| Recommended buffer-size setting              | Any       | Any       | Any       | Not too large |
| Recommended vfs-read-ahead setting           | Any       | Any       | Any       | Large if required |

Key points:
- off is the default mode and uses no disk caching, which can limit some file operations.
- minimal caches files opened for both read and write, but still has some limitations.
- writes caches write operations and supports most normal file system operations.
- full caches all reads and writes, supports all normal file system operations, and offers additional features like sparse files and read-ahead buffering.

Choosing the best mode depends on your specific needs and priorities. Consider factors such as:
- The types of file operations you need to support
- The importance of performance
- The amount of available disk space
- Your tolerance for potential data loss in case of unexpected shutdowns

## 指纹和`--vfs-fast-fingerprint`

计算文件指纹的方式：
- size
- modification time
- hash


**hash is slow with the local and sftp backends as they have to read the entire file and hash it, and modtime is slow with the s3, swift, ftp and qinqstor backends because they need to do an extra API call to fetch it.**

If you use the `--vfs-fast-fingerprint` flag then rclone will not include the slow operations in the fingerprint. This makes the fingerprinting less accurate but much faster and will improve the opening time of cached files.

If you are running a vfs cache over local, s3 or swift backends then using this flag is recommended.

## VFS Chunked Reading

以分块模式下载文件，减少流量消耗

```
--vfs-read-chunk-size SizeSuffix        Read the source objects in chunks (default 128M)
--vfs-read-chunk-size-limit SizeSuffix  Max chunk doubling size (default off)
```

## VFS 性能

```
--no-checksum     Don't compare checksums on up/download.
--no-modtime      Don't read/write the modification time (can speed things up).
--no-seek         Don't allow seeking in files.
--read-only       Only allow read-only access.
```

有时候 rclone 以非顺序的方式传递读取或写入操作。与其进行寻址，rclone 将等待一小段时间，以便按顺序读取或写入。
```
--vfs-read-wait duration   Time to wait for in-sequence read before seeking (default 20ms)
--vfs-write-wait duration  Time to wait for in-sequence write before giving error (default 1s)
```


`--transfers` 是 rclone 中用于设置同时运行的文件传输数目的选项。需要`--vfs-cache-mode`为writes或者full。
```
--transfers int  Number of file transfers to run in parallel (default 4)
```



