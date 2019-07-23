---
title: 解决vi和vscode中文显示乱码，以及聊聊字符编码
date: 2019-07-18 21:03:06
tags: [技巧]
categories: [技巧, linux]
keywords: [中文乱码, gbk, utf8, BOM, chcp, BOMInputStream]
description: 从ASCII、GB2312、GBK（对应cp936）到GB18030的编码方法是向下兼容的。而Unicode只与ASCII兼容。使用chcp查看windows代码页。BOM是为了解决UTF-16的编码识别问题，标准的UTF-8是不需要的，但是可以支持。Windows默认对UTF-8都加上BOM，会导致Linux软件处理出异常。java可以使用BOMInputStream处理包含BOM的文件。
---

域名备案要求显示站点内容，于是网上找了个静态页模板，再用nginx部署。需要在最下方需添加备案号且链接到工信部网站。

# vi

ssh服务器，vi加上去就好了。
但是，vi打开乱码了。。。不用想，肯定是编码问题。我的控制台是utf8编码，估计是文件用了gbk、gb2312之类的编码。

修改 `~/.vimrc` 文件
```bash
set fileencodings=utf-8,ucs-bom,gb18030,gbk,gb2312,cp936
set encoding=utf-8
set termencoding=utf-8
```
保存后再打开，中文显示就正常了。配置项意义如下：
- encoding：vi内部运行使用的编码
- fileencoding：写入文件时采用的编码类型。
- termencoding：输出到terminal采用的编码类型。

# vscode

备案信息是加上去了，但是刷新页面看，基本看不清，得手动调下css。索性把文件拷贝到本地编辑好了。
vscode打开又是乱码。。。尼玛，太矬了。。。
于是settings查找encoding配置，发现`Auto Guess Encoding`竟然是默认关闭，太不友好了。
{% asset_img vscode.png %}
嗯，这下终于正常了。顺便看了下右下角的文件编码：gb2312。

意外收获：安装xshell、xftp，打开xshell并且ssh登录后，`Ctrl`+`Alt`+`F`可以直接打开xftp，非常方便。

# 编码相关

既然今晚跟编码方式这么有缘，就顺手整理下编码相关的知识。
对于字符编码，通常关注编码方式（定长、变长、编码字节数、特殊控制字符）、支持字符数、和不同字符编码的兼容性。

## gb 2312

国家标准。1981年5月1日实施。
GB 2312 标准共收录 6763 个汉字，其中一级汉字 3755 个，二级汉字 3008 个；同时收录了包括拉丁字母、希腊字母、日文平假名及片假名字母、俄语西里尔字母在内的 682 个字符。（就是支持的字符少，不包括繁体字，但是能满足一般场景使用）
GB 2312 对任意一个图形字符都采用两个字节表示。

## big 5

维基上说：Big5是由台湾财团法人信息产业策进会为五大中文套装软件（并因此得名Big-5）所设计的中文共通内码，在1983年12月完成公告。那个之前还没有繁体字编码，GB2312又不含繁体字，因此才有了Big-5。
（想起以前玩游戏转换码的岁月）

## gbk

GBK是微软标准但不是国家标准。
GBK向下与GB 2312完全兼容。
GBK即汉字内码扩展规范，K为汉语拼音 Kuo Zhan（扩展）中“扩”字的声母。
GBK共收入21886个汉字和图形符号，包括：GB 2313、BIG 5、CJK字符（中日韩）等。
GBK采用双字节表示。

CJK是中日韩统一表意文字（CJK Unified Ideographs）。在Unicode中，收集各国相同的汉字，并且进行合并相同的编码点（code point）上，可以避免相同文字重复编码，浪费编码空间。

## gb 18030

GB 18030 与 GB 2312-1980 和 GBK 兼容，共收录汉字70244个。2000年，取代了GBK1.0的正式国家标准。
支持中国国内少数民族的文字，不需要动用造字区。
GB 18030 编码是一二四字节变长编码。

## code page，cp936

>Windows的内核已经采用Unicode编码，这样在内核上可以支持全世界所有的语言文字。但是由于现有的大量程序和文档都采用了某种特定语言的编码，例如GBK，Windows不可能不支持现有的编码，而全部改用Unicode。
>
>Windows使用代码页(code page)来适应各个国家和地区。code page可以被理解为前面提到的内码。GBK对应的code page是CP936。
>
>微软也为GB18030定义了code page：CP54936。但是由于GB18030有一部分4字节编码，而Windows的代码页只支持单字节和双字节编码，所以这个code page是无法真正使用的。

查看Windows本地代码页，打开cmd
```bat
λ chcp
活动代码页: 936
```

## ISO 8859-1

又称Latin-1或“西欧语言”，是国际标准化组织内ISO/IEC 8859的第一个8位字符集。它以ASCII为基础，在空置的0xA0-0xFF的范围内，加入96个字母及符号，藉以供使用附加符号的拉丁字母语言使用。

## unicode、ucs、utf

Unicode也是一种字符编码方法，不过它是由国际组织设计，可以容纳全世界所有语言文字的编码方案。 Unicode的学名是 "Universal Multiple-Octet Coded Character Set"，简称为UCS。

UCS只是规定如何编码，并没有规定如何传输、保存这个编码。UTF-8、UTF-7、UTF-16都是被广泛接受的方案。UTF-8的一个特别的好处是它与ISO- 8859-1完全兼容。UTF是 “UCS Transformation Format”的缩写。

**UTF-8是Unicode的一种实现!**
**UTF-8是Unicode的一种实现!**
**UTF-8是Unicode的一种实现!**

## UTF的字节序和BOM

>UTF-8以字节为编码单元，没有字节序的问题。UTF-16以两个字节为编码单元，在解释一个UTF-16文本前，首先要弄清楚每个编码单>元的字节序。例如“奎”的 Unicode编码是594E，“乙”的Unicode编码是4E59。如果我们收到UTF-16字节流“594E”，那么这是“奎” >还是 “乙”？
>
>Unicode规范中推荐的标记字节顺序的方法是BOM。BOM不是“Bill Of Material”的BOM表，而是Byte Order Mark。BOM是一个有点>小聪明的想法：
>
>在UCS编码中有一个叫做"ZERO WIDTH NO- BREAK SPACE"的字符，它的编码是FEFF。而FFFE在UCS中是不存在的字符，所以不应该出现在实际传输中。UCS规范建议我们在传输字节流前，先传输字符"ZERO WIDTH NO-BREAK SPACE"。
>
>这样如果接收者收到FEFF，就表明这个字节流是Big-Endian的；如果收到FFFE，就表明这个字节流是Little-Endian的。因此字符"ZERO WIDTH NO- BREAK SPACE"又被称作BOM。UTF-8不需要BOM来表明字节顺序，但可以用BOM来表明编码方式。字符"ZERO WIDTH NO-BREAK SPACE"的UTF-8编码是EF BB BF（读者可以用我们前面介绍的编码方法验证一下）。所以如果接收者收到以EF BB BF开头的字节流，就知道这是UTF-8编码了。

BOM是为了解决UTF-16的双字节编码问题而设计的方案。UTF-8根本不需要BOM，但是也可以支持。
坑爹的是，Windows和linux对UTF-8 BOM的处理不一样。
**Windows打开文本文件，会识别是否有BOM字符；编辑过的utf8文件，都会加上BOM**（现在终于可以指定要不要BOM）。
**但是linux上的工具一般不对BOM做处理**，结果是被当作非法字符，出现诡异的问题，常见的是shell、python执行出错、java读取BOM文件异常。

以前还会用apache common的`BOMInputStream`来读取文件专门处理BOM。
```java
//Example 1 - Detect and exclude a UTF-8 BOM
BOMInputStream bomIn = new BOMInputStream(in);
if (bomIn.hasBOM()) {
    // has a UTF-8 BOM
}
```
具体可以参照[BOMInputStream API文档](http://commons.apache.org/proper/commons-io/apidocs/org/apache/commons/io/input/BOMInputStream.html)。

{% asset_img bom.png 不同编码的字节顺序标记的表示 %}

## 兼容性

从ASCII、GB2312、GBK（对应cp936）到GB18030的编码方法是向下兼容的。而Unicode只与ASCII兼容。

## 一个字符编码的例子

Windows的默认字符编码是GBK，对于跨平台编程不友好，可以参见这个例子
- {% post_link fix-intellij-properties-file-garbled %}

# 参考资料

- [GB2312、GBK、GB18030 这几种字符集的主要区别是什么？](https://www.zhihu.com/question/19677619)
- [字符集编码cp936、ANSI、UNICODE、UTF-8、GB2312、GBK、GB18030、DBCS、UCS](https://blog.csdn.net/wanghuiqi2008/article/details/8079071)
- [「带 BOM 的 UTF-8」和「无 BOM 的 UTF-8」有什么区别？网页代码一般使用哪个？](https://www.zhihu.com/question/20167122)