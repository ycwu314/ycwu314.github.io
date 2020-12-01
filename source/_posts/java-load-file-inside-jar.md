---
title: 加载在jar文件中的资源
date: 2020-12-01 11:21:33
tags: [java]
categories: [java]
keywords:
description: 访问jar内部文件，使用`getResourceAsStream`而非`getResource`。
---

访问jar内部文件，使用`getResourceAsStream()`而非`getResource()`。
<!-- more -->

重构了每日统计邮件代码，把原来硬编码在java代码的html模板，改写为mustache模板，并且放置在resources目录。
>src\main\resources\stat\star_daily_stat_mail.html

本地idea启动验证功能正常，但是打包jar文件后执行异常：
```
java.io.FileNotFoundException: file:/home/ubuntu/devops/deploy/prod/medical/medical.jar!/BOOT-INF/classes!/stat/star_daily_stat_mail.html (No such file or directory)
```

读取文件，使用了`Class.java`的`getResource`
```java
    public java.net.URL getResource(String name) {
        name = resolveName(name);
        ClassLoader cl = getClassLoader0();
        if (cl==null) {
            // A system class.
            return ClassLoader.getSystemResource(name);
        }
        return cl.getResource(name);
    }
```

还有一个功能相近的`getResourceAsStream`
```java
     public InputStream getResourceAsStream(String name) {
        name = resolveName(name);
        ClassLoader cl = getClassLoader0();
        if (cl==null) {
            // A system class.
            return ClassLoader.getSystemResourceAsStream(name);
        }
        return cl.getResourceAsStream(name);
    }
```

原来代码使用了`getResource()`获取URL，再构造File对象读取文件内容。
但是对于jar文件，URL地址不能被File识别。
因此要使用流的方式(`getResourceAsStream()`)访问jar内部的文件。


小结：
- getResource返回URL对象，由应用转换为File。但是在jar环境不能成功。
- getResourceAsStream在jar环境/非jar环境都能识别。



