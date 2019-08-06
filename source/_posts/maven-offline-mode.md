---
title: 记一次maven offline mode引发的问题
date: 2019-08-06 21:37:53
tags: [maven, 技巧, devops]
categories: [技巧]
keywords: [maven offline mode, idea work offline, dependency:go-offline, maven离线模式]
description: maven offline mode只使用本地仓库并且不检查网络。dependency:go-offline可以检查所有依赖并且提前下载，使得offline模式工作正常。maven -o使用离线模式
---

# 问题描述

前2天，老铁对接讯飞语音转文字api。讯飞使用gson做json转换，并且不兼容我们项目的FastJSON，必须引入gson包。
但是神奇的事情发生了。老铁电脑上gson依赖包是红色的。我本地是正常拉到jar包。

# 解决过程

对于maven拉取不到jar包，通常是
- 网络不好，访问maven central repo慢成狗
- 下载过程中出现异常，导致jar包损坏

首先检查`.m2`目录的`settings.xml`文件，发现使用的是默认中央仓库，肯定慢啦。
改为使用阿里云镜像，在mirrors节点增加一个镜像
```xml
<mirror>
	<id>alimaven</id>
	<name>aliyun maven</name>
	<url>http://maven.aliyun.com/nexus/content/groups/public/</url>
	<mirrorOf>central</mirrorOf> 
</mirror> 
```
再去idea构建，发现还是不成功。检查了`.m2\repository`目录，没有对应的gson目录。
肯定是某个环境配置的问题，但是一时半会想不到是哪里。。。先让他本地引入gson jar开发。

等开发完毕后，回头开始解决这个奇怪的问题。他有2台电脑，另一台电脑能够正常拉取gson包。
由于在idea操作maven，怀疑是idea maven配置问题。打开有惊喜
{% asset_img maven_work_offline.png %}
不能拉取gson包的电脑，开启了`work offline`。取消这个选项，重新拉取依赖，问题就解决。

# maven offline mode

以前没有接触maven离线模式，于是查资料了解。
maven offline mode，只使用本地仓库，不会从远程仓库拉取jar包。这就要求本地仓库要有所有的jar包！
maven offline mode的场景对于大多数人来说都是不适用的。我想下面的场景可能有用：
- 严格控制上网的地方，比如min gan行业的开发，只能使用本地仓库
- 连接central repo网路不好，不如直接本地仓库快。可以是一台能够快速连接central repo的电脑做代理，然后jar包都由它下载，并且放到共享的本地仓库。
- 没有网络，但是要构建项目，这时候强制使用本地仓库。比如高铁上。

# dependency:go-offline

来自《Apache Maven Cookbook》
>The go-offline goal of the Maven Dependency plugin downloads all the required dependencies and plugins for the project, based on the pom file. The –o option tells Maven to work offline and not check the Internet for anything.

正常使用maven offline mode的前提是，所有依赖包已经下载到本地。`dependency:go-offline`提供了这个功能
```
C:\workspace\medical>mvn dependency:go-offline
[INFO] Scanning for projects...
Downloading from alimaven: http://maven.aliyun.com/nexus/content/groups/public/org/apache/johnzon/johnzon-maven-plugin/1.1.11/johnzon-maven-plugin-1.1.11.pom
Downloaded from alimaven: http://maven.aliyun.com/nexus/content/groups/public/org/apache/johnzon/johnzon-maven-plugin/1.1.11/johnzon-maven-plugin-1.1.11.pom (3.6 kB at 2.7 kB/s)

// 省略一堆输出
[INFO] --------------------------------[ jar ]---------------------------------
[INFO]
[INFO] >>> maven-dependency-plugin:3.1.1:go-offline (default-cli) > :resolve-plugins @ medical >>>
[INFO]
[INFO] --- maven-dependency-plugin:3.1.1:resolve-plugins (resolve-plugins) @ medical ---
Downloading from alimaven: http://maven.aliyun.com/nexus/content/groups/public/org/apache/maven/reporting/maven-reporting-impl/2.3/maven-reporting-impl-2.3.pom
Downloaded from alimaven: http://maven.aliyun.com/nexus/content/groups/public/org/apache/maven/reporting/maven-reporting-impl/2.3/maven-reporting-impl-2.3.pom (5.0 kB at 10 kB/s)

// 省略一堆输出
[INFO] <<< maven-dependency-plugin:3.1.1:go-offline (default-cli) < :resolve-plugins @ medical <<<
[INFO]
[INFO]
[INFO] --- maven-dependency-plugin:3.1.1:go-offline (default-cli) @ medical ---
[INFO] Resolved: spring-boot-starter-aop-2.1.5.RELEASE.jar
[INFO] Resolved: spring-boot-starter-2.1.5.RELEASE.jar
// 省略一堆输出
```

构建的时候，使用`-o`参数指示maven离线工作，并且不检查网络
```
> mvn help
 -o,--offline                           Work offline
```

# 友情提示

不要手抖点击这个按钮，会开启offline mode
{% asset_img maven_offline_mode_button.png %}


# 小结

以后遇到maven依赖下载问题，要考虑
- central repo镜像配置
- 本地jar包损坏
- maven离线模式
