---
title: mybatis-pagehelper-with-multiple-datasource
date: 2020-01-15 19:58:04
tags: [mybatis, java]
categories: [mybatis]
keywords: [mybatis pagehelper 多数据源]
description: mybatis pagehelper 多数据源分页，要关闭PageHelperAutoConfiguration。
---


# 背景

系统中接入了mysql和postgres，使用mybatis作为ORM框架。需要支持分页，使用pagehelper插件。
<!-- more -->

# 区分不同的数据源配置

不同数据库分页格式不一样。因此要针对不同的数据库配置pagehelper。
因为有多个数据源，SqlSessionFactory、 DataSourceTransactionManager、 SqlSessionTemplate、 JdbcTemplate 等类要使用`@Qualifier`分别注入。

```java
@Bean(name = "pgSqlSessionFactory")
public SqlSessionFactory pgSqlSessionFactory(@Qualifier("pgDataSource") DataSource dataSource) throws Exception {
    SqlSessionFactoryBean bean = new SqlSessionFactoryBean();
    bean.setDataSource(dataSource);
    org.apache.ibatis.session.Configuration Configuration = new org.apache.ibatis.session.Configuration();
    boolean mapUnderscoreToCamelCase = false;
    if ("TRUE".equals(mapUnderscoreToCamelCase.toUpperCase())) {
        mapUnderscoreToCamelCase = true;
    }
    // 注意这里是PageInterceptor的拦截器，此处有伏笔
    Interceptor interceptor = new PageInterceptor();
    Properties properties = new Properties();
    //数据库,分页配置
    properties.setProperty("helperDialect", "postgresql");
    //是否分页合理化
    properties.setProperty("reasonable", "false");
    interceptor.setProperties(properties);
    bean.setPlugins(new Interceptor[] {interceptor});
    Configuration.setMapUnderscoreToCamelCase(mapUnderscoreToCamelCase);
    bean.setConfiguration(Configuration);
    bean.setMapperLocations(new PathMatchingResourcePatternResolver().getResources(mapperLocation));
    return bean.getObject();
}

@Bean(name = "pgJdbcTemplate")
public JdbcTemplate pgJdbcTemplate(@Qualifier("pgDataSource") DataSource dataSource) throws Exception {
    return new JdbcTemplate(dataSource);
}

```
方言列表见 [PageAutoDialect](https://github.com/pagehelper/Mybatis-PageHelper/blob/master/src/main/java/com/github/pagehelper/page/PageAutoDialect.java#L58)。


# 解决："在系统中发现了多个分页插件"

直接启动没问题，但是真正查询的时候报错：
```
org.mybatis.spring.MyBatisSystemException: nested exception is org.apache.ibatis.exceptions.PersistenceException: 
### Error querying database.  Cause: java.lang.RuntimeException: 在系统中发现了多个分页插件，请检查系统配置!
```

pagehelper插件通过`pagehelper-spring-boot-starter`依赖引入。
会自动引入`PageHelperAutoConfiguration`自动配置类：
```java
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
```
因为原来配置文件已经有pagehelper：
```yaml
pagehelper:
  helperDialect: mysql
  reasonable: true
  supportMethodsArguments: true
  params: count=countSql
```
导致加入了2个PageInterceptor。

解决方法：
- 屏蔽掉 PageHelperAutoConfiguration，同时删除多余配置

```java
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class, PageHelperAutoConfiguration.class})
```


