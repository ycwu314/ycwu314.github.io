---
title: elasticsearch match vs term, filter vs query
date: 2020-04-08 16:55:17
tags: [elasticsearch]
categories: [elasticsearch]
keywords: [elasticsearch match vs term, elasticsearch filter vs query]
description: elasticsearch match 和 term、 filter 和 query 笔记。
---

elasticsearch match 和 term、 filter 和 query 笔记。
<!-- more -->

# match vs term

## match

match是全文检索。传入的文本，先被分析（analyzed），再匹配索引。

## term

term是精确匹配。
term query不会对传入的文本分析（analyzed）。
不要在text类型上使用term query。因为text类型落盘的时候会被分析(analyzed)，导致term query很难匹配上。

ps. 标准分析器（standard analyzer）对text类型的分析步骤：
- Removes most punctuation (标点)
- Divides the remaining content into individual words, called **tokens** （分词）
- **Lowercases** the tokens

# query vs filter

## query

query会对检索文档进行相关性打分(涉及TF/IDF)，结果保存在`_score`字段，单精度浮点数。并且排序。
query结果不会缓存。

## filter

filter用于过滤文档（**是/否**满足过滤条件），不会对文档打分。通常比query快。
filter结果可以使用缓存。
filter cache 是节点层面的缓存设置，每个节点上所有数据在响应请求时，是共用一个缓存空间的。当空间用满，按照 LRU 策略淘汰掉最冷的数据。

ES 2.0以后把filter和query合并。

## constant_score

当我们不关心检索词频率TF（Term Frequency）对搜索结果排序的影响时，可以使用constant_score将查询语句query或者过滤语句filter包装起来。
```
GET /_search
{
    "query": {
        "constant_score" : {
            "filter" : {
                "term" : { "user" : "kimchy"}
            },
            "boost" : 1.2
        }
    }
}
```

# 小结

- text类型使用match全文检索。
- query 是要相关性评分的，filter 不要；
- query 结果无法缓存，filter 可以。
- 全文搜索、评分排序，使用 query；
- 是非过滤，精确匹配，使用 filter。

# 参考

- [query-dsl-term-query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-term-query.html)
- [queries_and_filters](https://www.elastic.co/guide/en/elasticsearch/guide/current/_queries_and_filters.html#_performance_differences)