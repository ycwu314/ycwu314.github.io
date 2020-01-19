---
title: yaml 笔记
date: 2020-01-19 11:08:07
tags: [yaml]
categories: [yaml]
keywords: [yaml]
description: 一些yaml格式使用笔记。
---

最近修改yaml比较多，记录使用笔记。
<!-- more -->

# 用冒号和空格表示键值对 `key: value`

kubernates yaml 文件报错：
>error: yaml: line 2: mapping values are not allowed in this context

`key: value`，注意在value和“:"之间要有一个空格。


# 编码

springboot yaml 文件报错：
```
Caused by: org.yaml.snakeyaml.error.YAMLException: java.nio.charset.MalformedInputException: Input length = 1
```
指定配置文件编码不是UTF-8的，转换成UTF-8就行了。


# 特殊符号

## 引号
简单数据（scalars，标量数据）可以不使用引号括起来，包括字符串数据。用单引号或者双引号括起来的被当作字符串数据，在单引号或双引号中使用C风格的转义字符

springboot yaml报错
```yaml
management:
  endpoints:
    web:
      exposure:
        include: *   # 注意这里少了引号
```		
报错：
```
expected alphabetic or numeric character, but found 
(10)
 in 'reader', line 33, column 19:
            include: *
                      ^
```

改为`"*"`即可。

## tab

kubernates yaml报错：
>error: yaml: line 3: found character that cannot start any token

YAML文件里面不能出现tab键。