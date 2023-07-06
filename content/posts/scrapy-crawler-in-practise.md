---
title: scrapy 爬虫经历
date: 2019-12-21 11:50:36
tags: [scrapy, python, 爬虫]
categories: [python]
keywords: [scrapy, python, 爬虫]
description: 记录scrapy cloudflare防护、多级页面爬取、xpath定位等经验。
---

# 前言

因为版权原因，在线听歌越来越麻烦，于是开始自建一个小乐库，纯属自用。
记录一下爬取经历。

<!-- more -->

# 突破首页防卫

用在线工具测试好了首页xpath提取表达式，UserAgent什么的都设置了，但是在scrapy执行一直报错。
于是curl一下首页，不开心了：
```html
<html>
<head>
<script language="javascript">setTimeout("try{setCookie();}catch(error){};location.replace(location.href.split(\"#\")[0])",2000);</script>
<script type="text/javascript" src="http://********:80/usershare/flash.js"></script>
<script type="text/javascript">var ret=getIPs(function(ip){rtcsetcookie(ip)});checkflash(ret)</script>
</head>
<body>
        <object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" codebase="http://fpdownload.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=7,0,0,0" width="0" height="0" id="m" align="center">
                <param name="allowScriptAccess" value="always"/><param name="movie" value="http://********:80/usershare/1.swf"/><param name="quality" value="high" />
                <embed src="http://********:80/usershare/1.swf" quality="high" width="0" height="0"  name="m" align="center" allowScriptAccess="always" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.co
m/go/getflashplayer"/></object>
</body>
</html>
```

计算cookie，然后loadpage得到加载页面。
js文件没有混淆，可以模拟计算，或者用JavaScript插件执行。
不过在浏览器看了请求参数，发现
```
'Cookie': '__cfduid=dcbd0294352d18643417ae3aa8bbdd8fe1576674941; blk=0; jploop=false; jpvolume=0.923'
```
[__cfduid](https://support.cloudflare.com/hc/en-us/articles/200170156-Understanding-the-Cloudflare-Cookies)，那是用了cloudflare防护。想起来了，之前偶尔打开也遇到5秒钟防护盾的页面。

```
The _cfduid cookie collects and anonymizes End User IP addresses using a one-way hash of certain values so they cannot be personally identified. The cookie is a session cookie that expires after 30 days.
```
于是找到[cloudflare-scrape](https://github.com/Anorov/cloudflare-scrape)模块
>A simple Python module to bypass Cloudflare's anti-bot page (also known as "I'm Under Attack Mode", or IUAM), implemented with Requests. 


看能不能绕过去，得到真实的首页:

```python
import cfscrape

    def __init__(self):
        # returns a CloudflareScraper instance
        self.scraper = cfscrape.create_scraper(delay=5)

    def start_requests(self):
        url = 'xxxx'
        text = self.scraper.get(url).text    
```
可是报错了
```
  File "c:\users\xxx\pycharmprojects\scrapy_learn\venv\lib\site-packages\cfscrape\__init__.py", line 351, in get_tokens
    'Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM ("I\'m Under Attack Mode") enabled?'
ValueError: Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM ("I'm Under Attack Mode") enabled?
```

试了一下，先手动打开访问一次网页，再用CloudflareScraper解析，就可以正常访问首页数据，具体原因还没想明白，先用着
```python
    def start_requests(self):
        url = 'xxxx'
        r = requests.get(url)
        r.close()
        text = self.scraper.get(url).text
```

# 多级爬取

爬取思路：
- 首页解析音乐类别列表（genre列表）
- 分页爬取每个音乐类别的歌曲列表（play list列表）
- 爬取每个歌曲播放页面的元数据（play music列表）

整个爬取流程经历：
>首页->音乐分类->歌曲列表->歌曲页面

最终要解析元数据的页面是歌曲页面。但是要经历前面3个页面，才能遍历全量的歌曲页面地址。
scrapy的`start_requests`方法用于初始化爬取网页url。以前写简单的页面爬取，直接在`parse`方法做最终页面的解析即可。难道要在`parse`方法塞几个页面的解析逻辑？
Off course not! 
scrapy的Request支持callback。不同页面的设置不同回调函数解析即可。
```python
yield Request(play_music_page_url, headers=self.headers, callback=self.parse_music, meta=meta)
```


# 分页爬取上下文

分页爬取，直接读取接口
```
http://xxxx/genre/musicList/{genre}?pageIndex={pageIdx}&pageSize=20&order=hot
```
有个小问题，pageIdx要用来计算下一次的页码。
可以用正则提取。但是scrapy Request提供了meta对象，用来保留多次爬取的上下文，非常方便。
发送meta
```python
yield Request(str.format(self.GENRE_DETAIL_TEMPLATE, genre_idx, page_idx), headers=self.headers, meta={
    "genre_idx": genre_idx,
    "page_idx": page_idx,
    "genre": tag
})
```
读取meta
```python
next_page_idx = response.meta['page_idx'] + 1
genre_idx = response.meta['genre_idx']
```

# xpath解析

解析音乐文件路径，发现url不是写在某个属性，而是在script里面拼接。
```js
    <script type="text/javascript">
        var format = "mp3";
        var PageData = {};
        PageData.Host="xxxxx";
        PageData.DownHost="xxxxx";
        PageData.down="down7";
        PageData.musicId = "33";
        PageData.likeCount = "1221";
        PageData.commentCount = 176;
        PageData.day=20;
        PageData.code=12;
        PageData.format="mp3";
        var ip="xxxxx";
        var fileHost="xxxxx";
        var musicHost="xxxxx";
        var isCMobile=isMobileIp(ip) && window.isCMIp;
        setItem("cm",isCMobile);
        var mp3="33/mp3/12";
        mp3=fileHost+mp3;
        var bdText = "清晨(New Morning) - 班得瑞";
        var bdText2 = "分享一首好听的轻音乐：" + bdText;
        var imgUrl="xxxxx";
    </script>
```

首先要定位这个script，发现xpath表达式在页面工具和scrapy解析有兼容性问题，单纯计算script index定位的结果不一致😂。
那就用文本匹配。涉及2个xpath函数：
- contains()：匹配一个属性值中包含的字符串
- text()：显示文本信息

定位script标签，再转为文本做正则匹配即可。
```python
script = str(response.xpath('//script[contains(text(), "var mp3=")]').extract()[0])
match = re.search('mp3=".+";', script)
```
同样方式得到fileHost等属性。


另外，提取标题的时候，发现元数据出现多个空格，正则解决
```python
re.sub(' +', ' ', title)
```
