---
title: springmvc war 配置外部化
date: 2019-12-16 11:18:07
tags: [springmvc, spring]
categories: [spring]
keywords: [springmvc 配置 外部, PropertyPlaceholderConfigurer]
description: springmvc war 读取外部配置，可以使用`-D`传入。PropertyPlaceholderConfigurer支持一个实例，多个实例会报错。
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

# 解析多个properties文件

spring容器中最多只能定义一个`context:property-placeholder`，否则会报错：
```
Could not resolve placeholder 'moduleb.jdbc.driverClassName' in string value "${moduleb.jdbc.driverClassName}"
```

原因：Spring容器采用反射扫描的发现机制，在探测到Spring容器中有一个org.springframework.beans.factory.config.PropertyPlaceholderConfigurer的Bean就会停止对剩余PropertyPlaceholderConfigurer的扫描。

## util:properties

`util:properties`支持多个配置文件，`location`字段传入逗号分隔的列表即可。
```xml
<util:properties id="appProperties" location="${cas.properties.filepath:/WEB-INF/cas.properties},file:${catalina.base}/conf/jdbc.properties"/>
```

## propertyConfigurer

```xml
    <!-- 将多个配置文件位置放到列表中 -->
    <bean id="propertyResources" class="java.util.ArrayList">
        <constructor-arg>
            <list>
                <!-- 这里支持多种寻址方式：classpath和file -->
               <value>${cas.properties.filepath:/WEB-INF/cas.properties}</value>
                <!-- 推荐使用file的方式引入，这样可以将配置和代码分离 -->
                <value>file:${catalina.base}/conf/app.properties</value>
            </list>
        </constructor-arg>
    </bean>

    <!-- 将配置文件读取到容器中，交给Spring管理 -->
    <bean id="propertyConfigurer" class="org.springframework.beans.factory.config.PropertyPlaceholderConfigurer">
        <property name="locations" ref="propertyResources" />
    </bean>
```