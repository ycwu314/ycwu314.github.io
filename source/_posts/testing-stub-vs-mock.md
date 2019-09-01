---
title: 测试用例中stub和mock的区别
date: 2019-07-15 23:33:53
tags: [测试, 微服务]
categories: [测试]
keywords: [stub, mock, 微服务测试, test double]
description:
---

今晚看《微服务设计》关于测试的章节，发现平时对stub和mock理解比较模糊，于是整理下资料。
<!-- more -->
# test double

stub和mock都属于test double（替身）。《xUnit Test Patterns》这本书提到了5种test double：
- dummy
- fake
- stub
- spy
- mock

## dummy

>Dummy objects are passed around but never actually used. Usually they are just used to fill parameter lists.

dummy的唯一用途是填充参数，使得编译可以通过。

##  fake

>Fakes are objects that have working implementations, but not same as production one. Usually they take some shortcut and have simplified version of production code.

fake是一种完整功能的实现，但是通常不会用于生产环境。使用fake的原因是更加便捷，例如更简单的配置、更快的启动速度、更快的响应速度、更简单的数据清理等。常见的例子是使用in memory database（例如h2）代替生产环境的数据库实现（例如mysql）。

## stub

>Stub is an object that holds predefined data and uses it to answer calls during tests. It is used when we cannot or don’t want to involve objects that would answer with real data or have undesirable side effects.

stub是测试用例会使用到的、预先定义(predefined)的数据。通常在只读场景使用stub，无法获得真实数据的返回，或者根本不关心返回数据。
例如，测试一个服务A，它从推荐服务获取数据，再组装。那么服务A不需要关心推荐服务返回的真实数据，可以返回几个hardcode数据即可。

## spy

>Spies are stubs that also record some information based on how they were called. One form of this might be an email service that records how many messages it was sent.

spy对象记录方法调用情况。Martin Folwer这个解释比较模糊，跟下面提到的mock容易混淆。

## mock

>Mocks are objects that register calls they receive.
In test assertion we can verify on Mocks that all expected actions were performed.

mock会记录所有调用情况。通过测试断言，检查mock提供了期望的行为。
典型的场景是，不想调用真实的代码，或者真实代码不方便检查其执行结果（比如返回类型是void、调用外部服务提供的接口）。
比如下单场景，要调用支付网关接口。

# stub vs mock

上面对stub和mock的解释已经比较清楚了。
stub不关心返回结果、或者难以获取真实的返回结果，通常用于只读场景的返回。
mock关注每次调用的情况，提供预定行为的返回，并且可以被断言检查。mock关注对行为的检查。

```java
 //stubbing using built-in anyInt() argument matcher
 when(mockedList.get(anyInt())).thenReturn("element");

 //stubbing using custom matcher (let's say isValid() returns your own matcher implementation):
 when(mockedList.contains(argThat(isValid()))).thenReturn("element");

 //following prints "element"
 System.out.println(mockedList.get(999));

 //you can also verify using an argument matcher
 verify(mockedList).get(anyInt());

 //argument matchers can also be written as Java 8 Lambdas
 verify(mockedList).add(argThat(someString -> someString.length() > 5));
```

# spy vs mock

spy和mock都会记录方法的调用情况，容易混淆。如果结合Mockito的使用方式，就比较清晰了。

[mockito spy文档](https://static.javadoc.io/org.mockito/mockito-core/3.0.0/org/mockito/Mockito.html#13)
>You can create spies of real objects. When you use the spy then the real methods are called (unless a method was stubbed).
>Real spies should be used carefully and occasionally, for example when dealing with legacy code.
>Spying on real objects can be associated with "partial mocking" concept.

**spy指向真实对象，可以对部分方法进行mock（partial mocking）。相反，mock需要对所有使用到的方法进行stubbing。**

比如一个外部依赖服务包含a、b、c三个方法。如果要采用a、b方法的真实实现，并且使用c的mock实现，用spy就可以了。
如果使用mock，则需要对a、b、c三个方法做处理。

# 可信依赖和隔离

面试新人的时候，问“为什么会在单元测试用例里面做mock”，经常得到的回答是环境配置方便之类，其实没有回答到点子上。
test double的思想是，外部服务（比如未经良好测试的代码）可能不可靠的，会影响当前对象的测试产生影响，因此要隔离。
为什么不对java.lang.String类做mock？因为通常情况下，自己写的代码，不会因为String类的缺陷导致失败，或者说，信任String类。

# 参考资料

- [Test Doubles — Fakes, Mocks and Stubs.](https://blog.pragmatists.com/test-doubles-fakes-mocks-and-stubs-1a7491dfa3da)
- [Martin Fowler的TestDouble](https://martinfowler.com/bliki/TestDouble.html)


