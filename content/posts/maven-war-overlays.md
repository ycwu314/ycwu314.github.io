---
title: maven war overlays 机制
date: 2019-12-12 17:40:40
tags: [maven, CAS]
categories: [maven]
keywords: [maven war overlays]
description: overlay机制能够方便进行二次开发，减少源码管理和跟踪的复杂度，降低入侵性，方便升级主干版本。
---

# maven war overlay

最近学习CAS系统，发现CAS推荐使用overlay方式进行定制。
一般的定制化开发，可能要修改某个页面、修改某个功能实现，为此clone整个开源项目做二次开发，这样做法比较重型，侵入性太强，不利于以后升级主干版本。
其中一种解决思路是，在原来开源项目的基础上，单独修改某些实现，打包的时候再合并替换掉。
maven的war overlay机制实现了上面的功能。
overlay可以把多个项目war合并成为一个项目，并且如果项目存在同名文件，那么主项目中的文件将覆盖掉其他项目的同名文件。

<!-- more -->

# 以CAS为例子

2个概念：
- 主项目：pom文件开启overlay配置的项目，通常是二次开发源码的项目。
- 从项目：基础项目。如果主项目和从项目出现相同路径、相同名字的文件，那么从项目的内容会被主项目替换掉。这个例子里面是`cas-server-webapp`项目。

## 创建主项目

cas-server-overlays-demo

## 引入从项目

CAS的定制开发，会使用`cas-server-webapp`作为从项目。

```xml
<dependency>
       <groupId>org.jasig.cas</groupId>
       <artifactId>cas-server-webapp</artifactId>
       <version>${cas.version}</version>
       <type>war</type>
       <scope>runtime</scope>
</dependency>
```

## 配置maven overlay

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-war-plugin</artifactId>
    <version>3.2.3</version>
    <configuration>
        <failOnMissingWebXml>false</failOnMissingWebXml>
        <warName>cas</warName>
        <overlays>
            <overlay>
                <groupId>org.jasig.cas</groupId>
                <artifactId>cas-server-webapp</artifactId>
            </overlay>
        </overlays>
    </configuration>
</plugin>
```
maven-war-plugin默认要求打包的时候要有web.xml文件。因此关闭了`failOnMissingWebXml`选项。

## 修改 finalName

```xml
<finalName>cas</finalName>
```

## 定制化开发

比如定制化登录页，index.jsp。
注意定制化文件，路径和文件名必须要和`cas-server-webapp`项目一致，否则不生效。

# pros and cons

overlay的优点：
- 源代码修改的管理和跟踪非常轻量级
- 方便升级主干版本

overlay的缺点：
- 第一次配置有点繁琐

# 参考资料

- [WAR Overlay Installation](https://apereo.github.io/cas/6.0.x/installation/WAR-Overlay-Installation.html)
- [Overlays](http://maven.apache.org/plugins/maven-war-plugin/overlays.html)
