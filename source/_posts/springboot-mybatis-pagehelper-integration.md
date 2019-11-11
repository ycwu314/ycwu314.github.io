---
title: springboot集成Mybatis PageHelper不生效的case
date: 2019-11-11 18:26:28
tags: [springboot, mybatis]
categories: [springboot]
keywords:  [Mybatis PageHelper]
description: springboot可以使用pagehelper-spring-boot-starter集成PageHelper。
---

项目使用mybatis spring boot starter集成mybatis插件。增加PageHelper插件，拷贝网上集成pagerhelper的方法没有生效。
<!-- more -->
后来发现可以使用pagehelper springboot starter继承。记录下来做参考。
pom.xml配置如下：
```xml
<dependency>
    <groupId>com.github.pagehelper</groupId>
    <artifactId>pagehelper-spring-boot-starter</artifactId>
    <version>1.2.12</version>
</dependency>

<dependency>
    <groupId>org.mybatis.spring.boot</groupId>
    <artifactId>mybatis-spring-boot-starter</artifactId>
    <version>2.1.1</version>
</dependency>        
```
version修改为对应版本。

pagehelper-spring-boot-starter会自动引入pagehelper-spring-boot-autoconfigure和pagehelper依赖。
PageHelperAutoConfiguration类的addPageInterceptor()实现配置和加载插件。
```
@Configuration
@ConditionalOnBean(SqlSessionFactory.class)
@EnableConfigurationProperties(PageHelperProperties.class)
@AutoConfigureAfter(MybatisAutoConfiguration.class)
public class PageHelperAutoConfiguration {

    @Autowired
    private List<SqlSessionFactory> sqlSessionFactoryList;

    @Autowired
    private PageHelperProperties properties;

    /**
     * 接受分页插件额外的属性
     *
     * @return
     */
    @Bean
    @ConfigurationProperties(prefix = PageHelperProperties.PAGEHELPER_PREFIX)
    public Properties pageHelperProperties() {
        return new Properties();
    }

    @PostConstruct
    public void addPageInterceptor() {
        PageInterceptor interceptor = new PageInterceptor();
        Properties properties = new Properties();
        //先把一般方式配置的属性放进去
        properties.putAll(pageHelperProperties());
        //在把特殊配置放进去，由于close-conn 利用上面方式时，属性名就是 close-conn 而不是 closeConn，所以需要额外的一步
        properties.putAll(this.properties.getProperties());
        interceptor.setProperties(properties);
        for (SqlSessionFactory sqlSessionFactory : sqlSessionFactoryList) {
            sqlSessionFactory.getConfiguration().addInterceptor(interceptor);
        }
    }

}

```

