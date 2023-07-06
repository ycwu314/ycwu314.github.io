---
title: mybatis pagehelper插件自定义count sql
date: 2020-04-14 10:37:50
tags: [mybatis, java]
categories: [java]
keywords: [mybatis pagehelper count]
description: pagehelper默认的分页sql性能一般。现在支持自定义count sql。
---
# 背景

一个分页接口比较慢，需要返回当前页面数据和count总数。
系统中使用了pagehelper插件，这2个查询是串行执行，理想情况下是50:50的时间消耗。
于是想看下改成并发查询的效果。
<!-- more -->

# pagehelper分析

## pagehelper 新增支持自定义count sql

pagehelper默认count sql，是在原来sql的基础上，套上count（具体看下面的源码分析）
```sql
select count(0) from
(<原来的sql>) tmp_count
```
这样的问题是，内部sql select了一堆列，对于count来说是多余的。

pagehelper 5.0.4 增加自定义count sql支持：
- 增加 countSuffix count 查询后缀配置参数，该参数是针对 PageInterceptor 配置的，默认值为 _COUNT。

来自官网的例子：
```xml
<select id="selectLeftjoin" resultType="com.github.pagehelper.model.User">
    select a.id,b.name,a.py from user a
    left join user b on a.id = b.id
    order by a.id
</select>
<select id="selectLeftjoin_COUNT" resultType="Long">
    select count(distinct a.id) from user a
    left join user b on a.id = b.id
</select>
```

## PageInterceptor count分析

pagehelper的分页入口在PageInterceptor：
```java
public Object intercept(Invocation invocation) throws Throwable {
    try {
        // more code
        if (!this.dialect.skip(ms, parameter, rowBounds)) {
            if (this.dialect.beforeCount(ms, parameter, rowBounds)) {
                // 计算总数
                Long count = this.count(executor, ms, parameter, rowBounds, resultHandler, boundSql);
                if (!this.dialect.afterCount(count, parameter, rowBounds)) {
                    Object var12 = this.dialect.afterPage(new ArrayList(), parameter, rowBounds);
                    return var12;
                }
            }

            resultList = ExecutorUtil.pageQuery(this.dialect, executor, ms, parameter, rowBounds, resultHandler, boundSql, cacheKey);
        } else {
            resultList = executor.query(ms, parameter, rowBounds, resultHandler, cacheKey, boundSql);
        }

        // more code
    } finally {
        this.dialect.afterAll();
    }
}
```

```java
private Long count(Executor executor, MappedStatement ms, Object parameter, RowBounds rowBounds, ResultHandler resultHandler, BoundSql boundSql) throws SQLException {
    // 优先定制化count sql
    String countMsId = ms.getId() + this.countSuffix;
    MappedStatement countMs = ExecutorUtil.getExistedMappedStatement(ms.getConfiguration(), countMsId);
    Long count;
    if (countMs != null) {
        count = ExecutorUtil.executeManualCount(executor, countMs, parameter, boundSql, resultHandler);
    } else {
        countMs = (MappedStatement)this.msCountMap.get(countMsId);
        if (countMs == null) {
            countMs = MSUtils.newCountMappedStatement(ms, countMsId);
            this.msCountMap.put(countMsId, countMs);
        }
        // 自动拼装sql
        count = ExecutorUtil.executeAutoCount(this.dialect, executor, countMs, parameter, boundSql, rowBounds, resultHandler);
    }
    return count;
}
```

自动拼装count sql的工具类在ExecutorUtil：
```java
    public static Long executeAutoCount(Dialect dialect, Executor executor, MappedStatement countMs, Object parameter, BoundSql boundSql, RowBounds rowBounds, ResultHandler resultHandler) throws SQLException {
        Map<String, Object> additionalParameters = getAdditionalParameter(boundSql);
        CacheKey countKey = executor.createCacheKey(countMs, parameter, RowBounds.DEFAULT, boundSql);
        // 依赖不同数据库方言
        String countSql = dialect.getCountSql(countMs, boundSql, parameter, rowBounds, countKey);
        BoundSql countBoundSql = new BoundSql(countMs.getConfiguration(), countSql, boundSql.getParameterMappings(), parameter);
        Iterator var11 = additionalParameters.keySet().iterator();

        while(var11.hasNext()) {
            String key = (String)var11.next();
            countBoundSql.setAdditionalParameter(key, additionalParameters.get(key));
        }

        Object countResultList = executor.query(countMs, parameter, RowBounds.DEFAULT, resultHandler, countKey, countBoundSql);
        Long count = (Long)((List)countResultList).get(0);
        return count;
    }
```

针对大部分数据库的实现CountSqlParser：
```java
    public String getSimpleCountSql(String sql) {
        return this.getSimpleCountSql(sql, "0");
    }

    public String getSimpleCountSql(String sql, String name) {
        StringBuilder stringBuilder = new StringBuilder(sql.length() + 40);
        stringBuilder.append("select count(");
        stringBuilder.append(name);
        stringBuilder.append(") from (");
        stringBuilder.append(sql);
        stringBuilder.append(") tmp_count");
        return stringBuilder.toString();
    }
```
当主sql查询大量的列，那么会影响count sql性能。


# 解决问题

方案1：
- 提供`_COUNT` sql，由pagehelper自动触发
- 二次开发paghelper，在`intercept()`实现并发查询

方案2：
- 提供`_COUNT` sql
- 手写分页sql
- 在慢接口（2个）手动包装FutureTask查询count和分页内容。

显然方案1侵入性更少，只修改一个地方，但是对全局有影响。

先测试性能，发现性能提升大概20%-30%左右。耗时大的sql是底层数据库执行count，并行查询优化有限。
综合考虑，使用方案2，尽量减少二次开发的维护成本。

回到这个问题本身，现在考虑使用elasticsearch对查询字段落盘，查询count单独走ES返回。

