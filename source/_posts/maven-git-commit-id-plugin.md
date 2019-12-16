---
title: Maven插件之git-commit-id-plugin
date: 2019-12-16 20:29:51
tags: [maven]
categories: [maven]
keywords: [git-commit-id-plugin]
description: 
---

因为每次构建不一定会升级版本号，为了把artifact和版本对应起来，可以使用git-commit-id-plugin插件。
<!-- more -->

引入插件
```xml
<plugin>
    <groupId>pl.project13.maven</groupId>
    <artifactId>git-commit-id-plugin</artifactId>
    <version>4.0.0</version>
    <executions>
        <execution>
            <id>get-the-git-infos</id>
            <goals>
                <goal>revision</goal>
            </goals>
            <phase>initialize</phase>
        </execution>
    </executions>
    <configuration>
        <generateGitPropertiesFile>true</generateGitPropertiesFile>
        <generateGitPropertiesFilename>${project.build.outputDirectory}/git.properties</generateGitPropertiesFilename>
        <includeOnlyProperties>
            <includeOnlyProperty>^git.build.(time|version)$</includeOnlyProperty>
            <includeOnlyProperty>^git.commit.id.(abbrev|full)$</includeOnlyProperty>
        </includeOnlyProperties>
        <commitIdGenerationMode>full</commitIdGenerationMode>
    </configuration>
</plugin>
```

git-commit-id-plugin能够收集比较多的git信息，因此使用`includeOnlyProperties`指定需要保留的信息。

所有支持的属性参见：[GitCommitPropertyConstant.java](https://github.com/git-commit-id/maven-git-commit-id-plugin/blob/master/core/src/main/java/pl/project13/core/GitCommitPropertyConstant.java):
```java
public class GitCommitPropertyConstant {
  // these properties will be exposed to maven
  public static final String BRANCH = "branch";
  public static final String LOCAL_BRANCH_AHEAD = "local.branch.ahead";
  public static final String LOCAL_BRANCH_BEHIND = "local.branch.behind";
  public static final String DIRTY = "dirty";
  // only one of the following two will be exposed, depending on the commitIdGenerationMode
  public static final String COMMIT_ID_FLAT = "commit.id";
  public static final String COMMIT_ID_FULL = "commit.id.full";
  public static final String COMMIT_ID_ABBREV = "commit.id.abbrev";
  public static final String COMMIT_DESCRIBE = "commit.id.describe";
  public static final String COMMIT_SHORT_DESCRIBE = "commit.id.describe-short";
  public static final String BUILD_AUTHOR_NAME = "build.user.name";
  public static final String BUILD_AUTHOR_EMAIL = "build.user.email";
  public static final String BUILD_TIME = "build.time";
  public static final String BUILD_VERSION = "build.version";
  public static final String BUILD_HOST = "build.host";
  public static final String BUILD_NUMBER = "build.number";
  public static final String BUILD_NUMBER_UNIQUE = "build.number.unique";
  public static final String COMMIT_AUTHOR_NAME = "commit.user.name";
  public static final String COMMIT_AUTHOR_EMAIL = "commit.user.email";
  public static final String COMMIT_MESSAGE_FULL = "commit.message.full";
  public static final String COMMIT_MESSAGE_SHORT = "commit.message.short";
  public static final String COMMIT_TIME = "commit.time";
  public static final String REMOTE_ORIGIN_URL = "remote.origin.url";
  public static final String TAGS = "tags";
  public static final String CLOSEST_TAG_NAME = "closest.tag.name";
  public static final String CLOSEST_TAG_COMMIT_COUNT = "closest.tag.commit.count";
  public static final String TOTAL_COMMIT_COUNT = "total.commit.count";

}
```

这些变量可以在pom中使用，比如增加到artifact的文件名中：
```xml
<properties>
   <version.number>${git.commit.time}.${git.commit.id.abbrev}</version.number>
</properties>
```

完整使用手册参见：[using-the-plugin](https://github.com/git-commit-id/maven-git-commit-id-plugin/blob/master/maven/docs/using-the-plugin.md)

默认会在target/classess目录增加`git.properties`文件。


