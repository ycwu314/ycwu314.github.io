---
title: 迁移老web项目到springboot
date: 2019-12-11 18:23:54
tags: [springboot, java]
categories: [springboot]
keywords: [spring-boot-legacy, swagger2]
description:
---

# 背景

原来有个项目，传统的spring + war包部署，在开源基础上做了定制开发，现在接收过来了。
由于后续有继续开发维护的需要，期望引入springboot框架，使用swagger做api管理。
最初想用springboot java config完全重写，但是看到一堆xml bean/servlet配置，遂放弃，改用兼容已有web.xml。

<!-- more -->

# 引入spring-boot-legacy

[spring-boot-legacy](https://github.com/dsyer/spring-boot-legacy)是一个spring官方组件，用于把servlet 2.5应用迁移到springboot。支持解析web.xml。
注意GitHub里面的web.xml转换工具已经不可以访问了。

pom.xml：
```xml
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-legacy</artifactId>
      <version>2.1.0.RELEASE</version>
    </dependency>

    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-autoconfigure</artifactId>
      <version>2.1.3.RELEASE</version>
    </dependency>

    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-dependencies</artifactId>    
        <version>2.1.3.RELEASE</version>
        <type>pom</type>
        <scope>import</scope>
    </dependency>
```

启动类：
1. 增加引入原来的spring xml配置
```java
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class, SecurityAutoConfiguration.class})
@ImportResource(locations = {"classpath:/spring-configuration/all.xml"})
public class App {

    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}
```

web.xml：
1. 增加启动类，且注释掉原来contextConfigLocation的配置。
```xml
    <context-param>
        <param-name>contextConfigLocation</param-name>
        <param-value>com.xxx.cas.App</param-value>
    </context-param>
```

2. 增加SpringBootContextLoaderListener，去掉原来的ContextLoaderListener。
```xml
    <listener>
        <listener-class>org.springframework.boot.legacy.context.web.SpringBootContextLoaderListener</listener-class>
    </listener>
```

# 日志冲突

```
java.lang.IllegalArgumentException: LoggerFactory is not a Logback LoggerContext but Logback is on the classpath. Either remove Logback or the competing implementation (class org.slf4j.impl.CasLoggerFactory loaded from file:/C:/tool/apache-tomcat-8.5.49/webapps/cas/WEB-INF/lib/cas-server-core-4.1.1.jar). If you are using WebLogic you will need to add 'org.slf4j' to prefer-application-packages in WEB-INF/weblogic.xml Object of class [org.slf4j.impl.CasLoggerFactory] must be an instance of class ch.qos.logback.classic.LoggerContext
	at org.springframework.util.Assert.isInstanceOf(Assert.java:346)
```

Add exclusion to both the spring-boot-starter and spring-boot-starter-web to resolve the conflict.

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter</artifactId>
  <exclusions>
    <exclusion>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-logging</artifactId>
    </exclusion>
  </exclusions>
</dependency>

<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-web</artifactId>
  <exclusions>
    <exclusion>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-logging</artifactId>
    </exclusion>
  </exclusions>
</dependency>
```

# GenericApplicationListener

```
Caused by: java.lang.NoClassDefFoundError: org/springframework/context/event/GenericApplicationListener
```

[官网](https://docs.spring.io/spring/docs/current/javadoc-api/org/springframework/context/event/GenericApplicationListener.html)表示spring 4.2以后才支持。

解决：spring版本更新到5.1.5.RELEASE。

# WEB-INF 资源

```
class path resource [WEB-INF/spring-configuration/filters.xml] cannot be opened because it does not exist
```
问题：`@ImportResource`试了多种方式，不能访问WEB-INF目录下的xml。
解决：复制到resources目录

# spring security 4 csrf

CAS 4.x集成的是spring security 3。升级springboot 2.x后同时也升级到spring security 4。
Spring Security 4默认启用了CSRF保护功能，该功能在Spring Security 3时就已经存在，默认是不启用。

```
org.springframework.beans.factory.support.BeanDefinitionOverrideException: Invalid bean definition with name 'requestDataValueProcessor' defined in null: Cannot register bean definition [Root bean: class [org.springframework.security.web.servlet.support.csrf.CsrfRequestDataValueProcessor]; scope=; abstract=false; lazyInit=false; autowireMode=0; dependencyCheck=0; autowireCandidate=true; primary=false; factoryBeanName=null; factoryMethodName=null; initMethodName=null; destroyMethodName=null] for bean 'requestDataValueProcessor': There is already [Root bean: class [org.springframework.security.web.servlet.support.csrf.CsrfRequestDataValueProcessor]; scope=; abstract=false; lazyInit=false; autowireMode=0; dependencyCheck=0; autowireCandidate=true; primary=false; factoryBeanName=null; factoryMethodName=null; initMethodName=null; destroyMethodName=null] bound.
	at org.springframework.beans.factory.support.DefaultListableBeanFactory.registerBeanDefinition(DefaultListableBeanFactory.java:897)
```

解决：手动增加创建requestDataValueProcessor。
```xml
<bean id="requestDataValueProcessor" class="org.springframework.security.web.servlet.support.csrf.CsrfRequestDataValueProcessor"></bean>
```
# service文件

获取CAS service文件路径
```xml
@Bean
public ServiceRegistryDao serviceRegistryDao() throws IOException {
    return new JsonServiceRegistryDao(new File(AppConfig.class.getResource("/services").getFile()));
}
```

# allow-bean-definition-overriding

```
The bean 'userRepository', defined in null, could not be registered. A bean with that name has already been defined in file XXX and overriding is disabled.
```
允许覆盖bean定义。配置文件增加：
```
spring.main.allow-bean-definition-overriding=true
```

参见`DefaultListableBeanFactory.registerBeanDefinition()`
```java
BeanDefinition existingDefinition = this.beanDefinitionMap.get(beanName);
if (existingDefinition != null) {
	if (!isAllowBeanDefinitionOverriding()) {
		throw new BeanDefinitionOverrideException(beanName, beanDefinition, existingDefinition);
	}
  // more codes
}
```

# Cannot subclass final class

```
Caused by: java.lang.IllegalArgumentException: Cannot subclass final class org.jasig.cas.services.DefaultServicesManagerImpl
```
final类不可以被继承，因此不能被代理proxy。
CGLib也没戏，这是java规范定义的。

解决：
1. 复制一份类，去掉final，相应的引用路径修改。
2. 或者使用maven overlay方式打包。新类的路径不变。

# tomcat 日志乱码

windows默认编码是GBK。tomcat日志默认编码是UTF-8。因此乱码。

解决：修改tomcat目录的`conf/logging.properties`
```
java.util.logging.ConsoleHandler.encoding = GBK
```
# url mapping重复定义

```
Caused by: java.lang.IllegalArgumentException: The FilterChainProxy contains two filter chains using the matcher Ant [pattern='/status/**']. If you are using multiple <http> namespace elements, you must use a 'pattern' attribute to define the request patterns to which they apply.
	at org.springframework.security.config.http.DefaultFilterChainValidator.checkForDuplicateMatchers(DefaultFilterChainValidator.java:70)
```
web.xml 和加载的 securityContext.xml 重复定义。注释掉即可。

# ObjectPostProcessor

```
Parameter 0 of method setObjectPostProcessor in org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter required a bean of type 'org.springframework.security.config.annotation.ObjectPostProcessor' that could not be found.
```

关闭spring security自动配置。
```java
@EnableAutoConfiguration(exclude = {
        org.springframework.boot.autoconfigure.security.SecurityAutoConfiguration.class
})
```

# ServletContextListener 重复加载

```
Caused by: java.lang.IllegalArgumentException: Once the first ServletContextListener has been called, no more ServletContextListeners may be added.
```
ServletContextListener 重复加载。

# 不能为属性:[commandName]找到setter 方法

```
Caused by: org.apache.jasper.JasperException: /WEB-INF/view/jsp/default/ui/casLogin.jsp (行.: [75], 列: [20]) 不能为属性:[commandName]找到setter 方法.
```
原来项目使用了spring form标签，其中commandName已经废弃，已经被modelAttribute替代了，于是更改jsp文件中的标签：
```
<form:form method="post" id="fm1" commandName="${commandName}" htmlEscape="true">
```
修改为
```               
<form:form method="post" id="fm1" modelAttribute="${commandName}" htmlEscape="true">
```

# 集成swagger 2

pom.xml：
```xml
    <!-- Swagger2 -->
    <dependency>
      <groupId>io.springfox</groupId>
      <artifactId>springfox-swagger2</artifactId>
      <version>2.9.2</version>
    </dependency>
    <dependency>
      <groupId>io.springfox</groupId>
      <artifactId>springfox-swagger-ui</artifactId>
      <version>2.9.2</version>
    </dependency>
    <dependency>
      <groupId>com.github.xiaoymin</groupId>
      <artifactId>swagger-bootstrap-ui</artifactId>
      <version>1.9.2</version>
    </dependency>
```

java config：
```java
@Configuration
@EnableSwagger2
@EnableWebMvc
public class SwaggerConfig {

    @Bean
    public Docket api() {
        return new Docket(DocumentationType.SWAGGER_2)
                .select()
                .apis(RequestHandlerSelectors.basePackage("com.xxx.yyy.controller"))
                .build().apiInfo(apiInfo());
    }

    private ApiInfo apiInfo() {
        return new ApiInfoBuilder()
                .title("开放接口API")
                .description("HTTP对外开放接口")
                .version("1.0.0")
                .termsOfServiceUrl("http://xxx.xxx.com")
                .license("LICENSE")
                .licenseUrl("http://xxx.xxx.com")
                .build();
    }
}
```

web.xml放行swagger入口，写在CAS之前。
```xml
    <servlet-mapping>
        <servlet-name>default</servlet-name>
        <url-pattern>/swagger-ui.html</url-pattern>
    </servlet-mapping>
```


# swagger2 和 guava兼容性

按上面的配置，启动报错：

```
An attempt was made to call the method com.google.common.collect.FluentIterable.concat(Ljava/lang/Iterable;Ljava/lang/Iterable;)Lcom/google/common/collect/FluentIterable; but it does not exist. Its class, com.google.common.collect.FluentIterable, is available from the following locations:

    jar:file:/C:/tool/apache-tomcat-8.5.49/webapps/cas/WEB-INF/lib/guava-18.0.jar!/com/google/common/collect/FluentIterable.class
```
更换新的guava包即可
```xml
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>28.1-jre</version>
    </dependency>
```

