---
title: 反爬虫系列之8：cloudflare防爬方案
date: 2019-09-04 15:46:11
tags: [爬虫]
categories: [爬虫]
keywords: [爬虫]
description: 推酷爬虫还是继续非法爬取本站。cloudflare防火墙策略，拦截爬虫。
---

# 又是推酷爬虫

不幸的消息，推酷爬虫又来了。
{% asset_img tuicool-crawler.png 推酷爬虫 %}

打开html，发现字体反爬已经被破😭，直接解析为文字了：
{% asset_img font-crack.png 字体反爬被破 %}

不过图片保护还能用。
{% asset_img protect-image-url.png 图片保护 %}

另外，至今推酷官方邮件biz@tuicool.com一直没有回复。

<!-- more -->

现在的结论是：
- 推酷爬虫对我的小站应该是一周更新一次。
- 文章链接还是暴露。猜测是从首页遍历。
- 简单的一套转换字体映射名的方式，不保险。

低估了这个多年文章搬运工。

应对措施：
- 先把还没被爬的文章撤下
- 买了新域名，赶紧搞备案。直接nginx + iptables封杀


# cloudflare 防火墙策略防爬

（以下内容写于2天之后）
在阿里云买了域名之后，发现备案要求续费主机至少3个月以上。。。如果使用另一个开发账号的ECS去备案，又涉及到备案人和域名持有人的问题。

域名和备案，只是为了能在ecs上部署站点，并且使用nginx做waf。
如果有另外的方式能够实现waf，就可以防爬，不需要这么折腾。
搜索资料，发现cloudflare提供了一些waf功能。
于是新的方案出来：
1. 登录阿里云域名控制台，新域名`ycwu314.top`域名解析从万网，改为cloudflare nameserver。
```
ines.ns.cloudflare.com
ivan.ns.cloudflare.com
```

2. dns解析转移，要等待一段时间才生效。
```
# whois ycwu314.top | grep 'Name Server'
Name Server: ines.ns.cloudflare.com
Name Server: ivan.ns.cloudflare.com
```

3. 在cloudflare中增加A记录或者CNAME，指向github。
>Custom domains configured with A records
>If you configured your custom domain using an A record, your A record must point to one of the following IP addresses for HTTPS to work:
>
>185.199.108.153
>185.199.109.153
>185.199.110.153
>185.199.111.153

4. GitHub pages指向新的域名`ycwu314.top`。

5. 开启https。cf默认给站点提供了免费证书，并且开启了https，也支持强制https传输、hsts等特性。

6. 在cf中配置waf
{% asset_img cloudflare-firewall.png cloudflare防火墙 %}
纳尼，要付费用户才能使用。。。其实有隔壁的入口是免费的，可以配置5条规则
{% asset_img cloudflare-firewall-2.png cloudflare防火墙 %}


使用github pages自定义域名的另一个好处是，由github直接返回301做重定向，加快google索引转移权重。

# 解决cloudflare access log 问题

拦截爬虫请求，可以根据ip、user-agent拦截，通常是在nginx/apache的access log获取。
但是，cloudflare只有企业版用户才能获取（人民币玩家😂）。
不过我想到一个方法，增加一个防火墙rule，用于记录access log。
再从这个rule观察可疑的ip和user-agent。

在firewall、tools这个入口也可以配置ip、user-agent拦截，但是只能一个一个添加。
{% asset_img cloudflare-firewall-tools.png cloudflare防火墙 %}

Firewall Rules页面可以使用cf的语法，结合脚本生成拦截规则。但是生成的cf表达式要小于4KB，因此UA不能无限配置。具体语法使用很简单，看下官网介绍就可以了。
{% asset_img cloudflare-firewall-result.png cloudflare防火墙 %}

最大问题是不支持下载access log，目前只能人工看和分析。以后写个脚本，直接提取access log日志，方便做行为分析。

另外，使用cloudflare之后，速度比直连github page要慢一些。


# logflare.app

研究cloudflare功能的时候在app页面发现了好东西：logflare.app。
{% asset_img logflare-1.png logflare.app %}
logflare使用cloudflare worker（serverless应用），异步采集请求日志，不对页面请求发生影响。
logflare.app收集请求日志，并且和Google Data Studio集成。这就是我想要的access log，还有数据分析工具可以使用，太赞了！
{% asset_img logflare-2.png logflare.app %}
不过只有IP地址，没有地理信息，可以去IPInfo.io注册一个key，free plan一个月5w requests。


# 捕捉爬虫

剩下的就是发几篇占位符文章，尝试捕捉推酷爬虫了。

# github pages 自定义域名设置丢失

使用travis ci构建后，发现GitHub pages设置的自定义域名没了。
改为使用CNAME文件，还是没有生效。
发现17年的时候就有人汇报了这个问题：[Pushing changes to GitHub Pages branch removes custom domain setting #7538](https://github.com/travis-ci/travis-ci/issues/7538)。
travis ci官网fqdn选项：[deployment](https://docs.travis-ci.com/user/deployment/pages/)
```
deploy:
    - fqdn: Optional, sets a custom domain for your website, defaults to no custom domain support.
```
然而也没有用。
因为deploy是使用hexo d命令操作的。并非travis ci的deploy任务。
后来想起来，我是在源码目录建立的CNAME文件，构建完之后当然没有拷贝到master分支的根目录。
因为使用了next主题，直接把CNAME文件丢到`themes\next\source`。
