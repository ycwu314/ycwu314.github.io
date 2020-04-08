---
title: java validation groups 分组校验
date: 2020-04-08 10:04:14
tags: [java]
categories: [java]
keywords: [java validation groups]
description: java validator框架，支持groups属性对校验规则分组。这样一个字段可以根据group的不同，支持不同的校验规则。
---

# 背景

使用java validation 框架，其中一个DTO对象的字段，在不同场景下校验规则不一样。
<!-- more -->
例如，比如update的时候id字段不能为空，而插入的时候不对id校验。

# validation框架的groups属性

validation框架支持groups字段，解决这类问题。

1. 新建接口类，用于validator分组。

```java
public interface Insert {}

public interface Update {}
```

2. 对validator配置groups属性

```java
@Data
public class CameraDTO {
    
    @NotBlank(groups={Update.class})
    private String id;

    // more codes
}
```

3. 应用层使用@Validated和对应的groups。

spring应用
```java
@Validated(Update.class) CameraDTO cameraDTO
```

普通java应用
```java
@Test
public void test() {
    Validator validator = Validation
            .buildDefaultValidatorFactory().getValidator();
    CameraDTO cameraDTO = new CameraDTO();
    Set<ConstraintViolation<CameraDTO>> constraintViolations = validator.validate(cameraDTO, Update.class);
    Assertions.assertEquals(1, constraintViolations.size());
}
```

# @Valid 和 @Validated

这2个容易混淆。

`@Valid`是java validation标准。
```java
package javax.validation;

@Target({ElementType.METHOD, ElementType.FIELD, ElementType.CONSTRUCTOR, ElementType.PARAMETER, ElementType.TYPE_USE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface Valid {
}
```

`@Validated`是spring validation框架。
```java
package org.springframework.validation.annotation;

@Target({ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface Validated {
    Class<?>[] value() default {};
}
```

对比两者的`@Target`注解属性，`@Valid`应用范围更广。


