---
title: 反爬虫系列之6：nginx屏蔽user-agent
date: 2019-09-03 18:00:10
tags: [爬虫, nginx]
categories: [爬虫]
keywords: [nginx user agent]
description: 使用nginx屏蔽掉可疑的user agent。使用iptables屏蔽爬虫ip段。
---

等过段时间部署到ecs，就可以使用nginx提高防爬能力。最简单的方式是检查ua，因为使用HttpClient、urllib之类的ua非常容易识别。
在server块增加判断user-agent
```nginx
if ($http_user_agent = "") { return 403; }

#禁止Scrapy等工具的抓取
if ($http_user_agent ~* (Scrapy|Curl|HttpClient)) {
     return 403;
}

#禁止指定UA及UA为空的访问
if ($http_user_agent ~* "FeedDemon|Indy Library|Alexa Toolbar|AskTbFXTV|AhrefsBot|CrawlDaddy|CoolpadWebkit|Java|Feedly|UniversalFeedParser|ApacheBench|Microsoft URL Control|Swiftbot|ZmEu|oBot|jaunty|Python-urllib|lightDeckReports Bot|YYSpider|DigExt|HttpClient|MJ12bot|heritrix|EasouSpider|DotBot|Ezooms|^$" ) {
     return 403;             
}
```
网上找到一些常见的爬虫站点的user-agent
- [Apache/Nginx/PHP 屏蔽垃圾 UA 爬虫的方法](https://www.moewah.com/archives/12.html)
- [网上坏蜘蛛搜索引擎bot/spider等HTTP USER AGENT关键字一览(无重复,持续更新)](https://www.mr-fu.com/4532/)

ua本身就不可靠，更好的方式，根据ip访问频率查找异常ip进行封杀，直接使用iptables封掉ip段。
```
iptables -I INPUT -s 54.36.148.0/24 -j DROP
```
