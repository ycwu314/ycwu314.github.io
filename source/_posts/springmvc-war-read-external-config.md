---
title: springmvc war 配置外部化
date: 2019-12-16 11:18:07
tags: [springmvc, spring]
categories: [spring]
keywords: [springmvc 配置 外部]
description: springmvc war 读取外部配置，可以使用`-D`传入。
---

又是一个legacy项目，springmvc + war部署，xml beans配置文件，现在要镜像部署。原来配置文件写在`WEB-INF`目录，需要改成外部化方便修改、不需要重新构建镜像。
试了一下，有几种方式实现。
<!-- more -->

# 少量几个配置项

1. 启动参数增加： `-DIP_CONF=111.222.111.222`
2. beans配置文件使用`${}`注入

```xml
<bean id="aService" class="com.xxx.services.AService">
    <property name="ip" value="${IP_CONF}"></property>
</bean>
```

# 配置文件

和上面的例子相似。

1. 启动参数增加： `-Dip.config.file=/app/xxx/ip.properties`
2. beans配置文件使用`${}`注入

```xml
<util:properties id="ipProperties" location="${ip.config.file:/WEB-INF/ip.properties}"/>
```

这里增加了默认值。