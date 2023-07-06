---
title: elasticsearch keyword vs text
date: 2020-03-30 10:52:03
tags: [elasticsearch]
categories: [elasticsearch]
keywords: [elasticsearch keyword vs text]
description: keyword和text简单对比。
---

# 背景

问题背景：项目中使用ES存储用户信息，查询身份证末位包含X的，不能正常返回。
<!-- more -->

在elasticsearch中，文本类型主要有string、text、keyword。
其中，在es 2.x版本只有string类型。5.x以后把string字段设置为了过时字段，引入text，keyword类型。

# keyword

## 使用场景

来自官网的介绍（[keyword datatype](https://www.elastic.co/guide/en/elasticsearch/reference/7.6/keyword.html)）：
- A field to index structured content such as IDs, email addresses, hostnames, status codes, zip codes or tags.
- They are typically used for filtering (Find me all blog posts where status is published), for sorting, and for aggregations. **Keyword fields are only searchable by their exact value**.
- If you need to index full text content such as email bodies or product descriptions, it is likely that you should rather use a text field.

keyword查询，是精确值匹配。

```
# 基于ES 7.x环境
# 创建索引
PUT my_person
{
  "settings": {
    "number_of_shards": 1
  },
  "mappings": {
    "properties": {
      "ID_NUMBER": {
        "type": "keyword"
      }
    }
  }
}


# 插入数据
POST /my_person/_doc
{
  "ID_NUMBER": "61032219001017552X"
}

# term是精确匹配，直接从反向索引查询
GET my_person/_search
{
  "query": {
    "term": {
      "ID_NUMBER": "61032219001017552X"
    }
  }
}

# 留意这里使用了小写x
# match全文检索，对item进行相同处理后再查询倒排表。因此查询不出来。
GET my_person/_search
{
  "query": {
    "match": {
      "ID_NUMBER": "61032219001017552x"
    }
  }
}

# 留意这里使用了大写X
# 转换后的item和倒排表一致，可以返回结果。
GET my_person/_search
{
  "query": {
    "match": {
      "ID_NUMBER": "61032219001017552X"
    }
  }
}
```

# text

text是全文检索类型，会被analyzer解析，转换为norm之后再建立索引。

# 解决问题

因为使用keyword类型存储身份证，且写入的时候是大写X。未配置normalizer。那么ES把完整的身份证创建索引。
使用term query查询，传入身份证参数为小写的x。导致匹配不上。

解决方法有2个：
- 前台接口都增加转换为大写操作；每个接口都修改一遍。
- keyword字段，增加normalizer属性，对传入查询的关键字进行预处理。

# 扩展： normalizer属性

翻译自官网[normalizer](https://www.elastic.co/guide/en/elasticsearch/reference/current/normalizer.html)：
- normalizer属性，和analyzer类似，但是normalizer只会产生单个token。
- normalizer在索引keyword之前使用，并且在查询时对输入关键字使用相同的normalizer转换，再去检索索引。这个行为对`match`或者`term`查询有影响。

normalizer的用途是，输入的关键字和存储的索引，都经过相同的规范化处理。

因为term query是精确匹配查询索引。因此输入关键字和索引存在差异将不能匹配（比如大小写）。
match是全文检索，也是类似。

# 小结

- keyword：存储数据时候，不会分词，存储空间相对少些。通常用于过滤、排序、聚合。
- text：存储数据时候，会自动分词。text类型的字段不能用于排序, 也很少用于聚合。
