---
title: java FileLock 简介
date: 2020-01-13 20:32:14
tags: [java]
categories: [java]
keywords: [java FileLock]
description: FileLock 底层实现依赖于操作系统，理论上提供跨越不同进程、不同编程语言的文件锁(但不是保证)。
---

# 背景

在看nacos源码，发现读取文件的工具类`ConcurrentDiskUtil.getFileContent()`涉及了FileLock，做下笔记。
<!-- more -->

# FileLock 简介

FileLock是一种标记，代表文件中一部分区域的锁定。`A token representing a lock on a region of a file.`
FileLock底层实现依赖操作系统的文件锁语义。理论上，FileLock的语义是跨越不同进程、不同编程语言(但不是强制保证)。
>Java FileLock uses advisory (not mandatory) locks on many platforms.


FileLock和很多其他锁类似，可以是独占或者共享。
一旦获取了FileLock，内部状态为有效（`valid = true`），需要手动释放。

FileLock的成员比较简单。
```java
public abstract class FileLock implements AutoCloseable {

    private final Channel channel;
    private final long position;
    private final long size;
    private final boolean shared;

// more code
}
```

由于是abstract，真正使用的是FileLock的子类，sun提供了私有实现：
```java
package sun.nio.ch;

public class FileLockImpl extends FileLock {
    private volatile boolean valid = true;
```

真正使用，是通过FileChannel 或者 AsynchronousFileChannel 获取 FileLock。
```java
    public abstract FileLock lock(long position, long size, boolean shared)
        throws IOException;

    public abstract FileLock tryLock(long position, long size, boolean shared)
        throws IOException;    
```

# FileLock 使用例子

`ConcurrentDiskUtil.getFileContent()`
```java
    public static String getFileContent(File file, String charsetName)
        throws IOException {
        RandomAccessFile fis = null;
        FileLock rlock = null;
        try {
            fis = new RandomAccessFile(file, "r");
            FileChannel fcin = fis.getChannel();
            int i = 0;
            do {
                try {
                    rlock = fcin.tryLock(0L, Long.MAX_VALUE, true);
                } catch (Exception e) {
                    ++i;
                    if (i > RETRY_COUNT) {
                        LOGGER.error("read {} fail;retryed time:{}",
                            file.getName(), i);
                        throw new IOException("read " + file.getAbsolutePath()
                            + " conflict");
                    }
                    sleep(SLEEP_BASETIME * i);
                    LOGGER.warn("read {} conflict;retry time:{}", file.getName(),
                        i);
                }
            } while (null == rlock);
            int fileSize = (int)fcin.size();
            ByteBuffer byteBuffer = ByteBuffer.allocate(fileSize);
            fcin.read(byteBuffer);
            byteBuffer.flip();
            return byteBufferToString(byteBuffer, charsetName);
        } finally {
            if (rlock != null) {
                rlock.release();
                rlock = null;
            }
            if (fis != null) {
                fis.close();
                fis = null;
            }
        }
    }
```
和其他锁类似，应该在finally处保证释放锁。
