---
title: Java 获取泛型类型对象
date: 2019-11-14 11:10:50
tags: [java]
categories: [java]
keywords: [java ParameterizedType]
description: ParameterizedType对应泛型，其getActualTypeArguments()方法获取真实类型。
---

参数化类型，即泛型，在Java中对应ParameterizedType。
在对泛型的反射操作中，常见的是获取真实类型。
<!-- more -->

ParameterizedType有多个方法，其中getActualTypeArguments()返回真实的类型，返回的是数组，数组元素个数是泛型个数。
例如`Map<K,V>`，getActualTypeArguments()[0]对应K，getActualTypeArguments()[1]对应V。

一个简单的例子：
```java
public class A {

    List<String> getList() {
        return null;
    }

    public static void main(String[] args) {
        try {
            Method m1 = A.class.getDeclaredMethod("getList");
            System.out.println("return type:\t\t\t" + m1.getReturnType());
            System.out.println("generic return type:\t" + m1.getGenericReturnType());
            Type returnType = m1.getGenericReturnType();
            if (returnType instanceof ParameterizedType) {
                Type actualType = ((ParameterizedType) returnType).getActualTypeArguments()[0];
                System.out.println("actual type:\t\t\t" + actualType);
                System.out.println("raw type:\t\t\t\t" + ((ParameterizedType) returnType).getRawType());
                System.out.println("owner type:\t\t\t\t" + ((ParameterizedType) returnType).getOwnerType());
            }
        } catch (NoSuchMethodException e) {
            e.printStackTrace();
        }
    }
}
```
输出
```
return type:			interface java.util.List
generic return type:	java.util.List<java.lang.String>
actual type:			class java.lang.String
raw type:				interface java.util.List
owner type:				null
```

得到actualType之后，转换为Class对象后再实例化。
```
Class clz = (Class) actualType;
Object obj = clz.newInstance();
```



