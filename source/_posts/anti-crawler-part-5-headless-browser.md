---
title: 反爬虫系列之5：headless浏览器检测
date: 2019-09-03 11:18:05
tags: [爬虫, web, 网络安全]
categories: [爬虫]
keywords: [headless chrome]
description: 除了直接http请求抓取页面之外，还有使用headless浏览器的方式，通常用于动态页面爬取。
---

# 检测headless浏览器

静态站点比较少使用headless浏览器爬取。不过也顺带整理了一些资料。代码见附录。
<!-- more -->

## navigator.user-agent

user-agent是最基本的检查字段，也是最不可靠的。结合platform一起判断。
参照fingerprintjs2（以下简称为fp）的getHasLiedOs和getHasLiedBrowser一起使用。

## chrome

如果ua测试为chrome，则有chrome对象，且至少有：
- chrome.app
- chrome.csl
- chrome.loadTimes

## chrome headless

Chrome Headless默认的ua包含HeadlessChrome：
```
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/59.0.3071.115 Safari/537.36
```

## navigator.webdriver

桌面浏览器navigator.webdriver返回为undefined。这是个只读属性。

参照[Navigator.webdriver](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/webdriver)

>The navigator.webdriver property is true when in:
>Chrome
>The --enable-automation or the --headless flag is used.
>Firefox
>The marionette.enabled preference or --marionette flag is passed.

## navigator.language

navigator.languages、navigator.language必须存在。
并且navigator.languages[0]等于navigator.language。
参照fp的getHasLiedLanguages。

## navigator.plugins 和 navigator.mimeTypes

正常浏览器plugins和mimeTypes不为空，并且plugin的mimeTypes对于navigator.mimeTypes。
headless浏览器默认plugins为空。

## window的存储属性： sessionstorage  localStorage indexedDB

测试window.sessionStorage、window.localStorage、window.indexedDB是否存在。

## 屏幕尺寸

测试
```js
window.screen.width < window.screen.availWidth || window.screen.height < window.screen.availHeight
```

## webgl

来自[[译] 如何检测 Chrome Headless（无头浏览器）？](https://zhaoji.wang/how-to-detect-chrome-headless/)
>当使用 Linux 下的普通 Chrome 时，我获得的渲染器和供应商为：“Google SwiftShader” 和 “Google Inc.”。在无头模式下，我获得的渲染器值为 “Mesa OffScreen”，这是一种不渲染任何窗口的技术。供应商则为 “Brian Paul”，这个项目孵化了开源图形库 Mesa。

```js
var canvas = document.createElement('canvas');
var gl = canvas.getContext('webgl');
 
var debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
var vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
var renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
 
if(vendor == "Brian Paul" && renderer == "Mesa OffScreen") {
    console.log("Chrome headless detected");
}
```

## Modernizr库检测浏览器特性

Modernizr 库可以测试浏览器中是否支持各种 HTML 和 CSS 功能
```js
if(!Modernizr["hairline"]) {
    console.log("It may be Chrome headless");
}
```

## 加载失败的图片

来自[[译] 如何检测 Chrome Headless（无头浏览器）？](https://zhaoji.wang/how-to-detect-chrome-headless/)
>对于普通的 Chrome，这些加载失败的图片仍然具有宽度和高度，其具体值取决于浏览器的缩放情况，总之肯定不会是零。但是，在 Chrome Headless 中，这种图片的宽度和高度全部都为零。
```js
var body = document.getElementsByTagName("body")[0];
var image = document.createElement("img");
image.src = "http://ycwu314dottop.jg";
image.setAttribute("id", "fakeimage");
body.appendChild(image);
image.onerror = function(){
    if(image.width == 0 && image.height == 0) {
        console.log("Chrome headless detected");
    }
}
```

# 识别headless浏览器之后

一旦发现是headless浏览器，可以考虑：
- 跳转到默认处理页面
- 或者，使用验证码，避免误杀

google reCaptcha提供了免费的验证码服务，但是要有服务器端获取结果。
其实静态站点也可以使用，通过serverless函数方式，只要不超出免费额度。这里提供一份参考：[Protecting Your Website Forms With Serverless CAPTCHA](https://medium.com/codait/protecting-your-website-forms-with-serverless-captcha-27e3ed2794a0)。文章中的架构图如下：
{% asset_img serverless-recaptcha.webp "Architecture of a serverless Captcha" %}

接入Google reCaptcha方式见[recaptcha](https://www.google.com/recaptcha/admin/create)
选择v3版本，可以在国内使用。

未来有需要再搭建。

# 参考

- [无头浏览器反爬与反反爬](https://gaoconghui.github.io/2019/06/%E6%97%A0%E5%A4%B4%E6%B5%8F%E8%A7%88%E5%99%A8%E5%8F%8D%E7%88%AC%E4%B8%8E%E5%8F%8D%E5%8F%8D%E7%88%AC/)
- [反爬虫中chrome无头浏览器的几种检测与绕过方式](https://blog.csdn.net/Revivedsun/article/details/81785000)
- [[译] 如何检测 Chrome Headless（无头浏览器）？](https://zhaoji.wang/how-to-detect-chrome-headless/)
- [爬虫如何隐藏Headles-Chrome不被检测出来](https://mlln.cn/2019/07/05/%E7%88%AC%E8%99%AB%E5%A6%82%E4%BD%95%E9%9A%90%E8%97%8FHeadles-Chrome%E4%B8%8D%E8%A2%AB%E6%A3%80%E6%B5%8B%E5%87%BA%E6%9D%A5/)

# 附录

整理了上文headless浏览器检测代码备用。
```js
/**
 * begin copy from https://github.com/Valve/fingerprintjs2/blob/master/fingerprint2.js
 */
var getHasLiedLanguages = function () {
    // We check if navigator.language is equal to the first language of navigator.languages
    // navigator.languages is undefined on IE11 (and potentially older IEs)
    if (typeof navigator.languages !== 'undefined') {
        try {
            var firstLanguages = navigator.languages[0].substr(0, 2)
            if (firstLanguages !== navigator.language.substr(0, 2)) {
                return true
            }
        } catch (err) {
            return true
        }
    }
    return false
}

var getHasLiedResolution = function () {
    return window.screen.width < window.screen.availWidth || window.screen.height < window.screen.availHeight
}

var getHasLiedOs = function () {
    var userAgent = navigator.userAgent.toLowerCase()
    var oscpu = navigator.oscpu
    var platform = navigator.platform.toLowerCase()
    var os
    // We extract the OS from the user agent (respect the order of the if else if statement)
    if (userAgent.indexOf('windows phone') >= 0) {
        os = 'Windows Phone'
    } else if (userAgent.indexOf('win') >= 0) {
        os = 'Windows'
    } else if (userAgent.indexOf('android') >= 0) {
        os = 'Android'
    } else if (userAgent.indexOf('linux') >= 0 || userAgent.indexOf('cros') >= 0) {
        os = 'Linux'
    } else if (userAgent.indexOf('iphone') >= 0 || userAgent.indexOf('ipad') >= 0) {
        os = 'iOS'
    } else if (userAgent.indexOf('mac') >= 0) {
        os = 'Mac'
    } else {
        os = 'Other'
    }
    // We detect if the person uses a mobile device
    var mobileDevice = (('ontouchstart' in window) ||
        (navigator.maxTouchPoints > 0) ||
        (navigator.msMaxTouchPoints > 0))

    if (mobileDevice && os !== 'Windows Phone' && os !== 'Android' && os !== 'iOS' && os !== 'Other') {
        return true
    }

    // We compare oscpu with the OS extracted from the UA
    if (typeof oscpu !== 'undefined') {
        oscpu = oscpu.toLowerCase()
        if (oscpu.indexOf('win') >= 0 && os !== 'Windows' && os !== 'Windows Phone') {
            return true
        } else if (oscpu.indexOf('linux') >= 0 && os !== 'Linux' && os !== 'Android') {
            return true
        } else if (oscpu.indexOf('mac') >= 0 && os !== 'Mac' && os !== 'iOS') {
            return true
        } else if ((oscpu.indexOf('win') === -1 && oscpu.indexOf('linux') === -1 && oscpu.indexOf('mac') === -1) !==
            (os === 'Other')) {
            return true
        }
    }

    // We compare platform with the OS extracted from the UA
    if (platform.indexOf('win') >= 0 && os !== 'Windows' && os !== 'Windows Phone') {
        return true
    } else if ((platform.indexOf('linux') >= 0 || platform.indexOf('android') >= 0 || platform.indexOf('pike') >= 0) &&
        os !== 'Linux' && os !== 'Android') {
        return true
    } else if ((platform.indexOf('mac') >= 0 || platform.indexOf('ipad') >= 0 || platform.indexOf('ipod') >= 0 ||
            platform.indexOf('iphone') >= 0) && os !== 'Mac' && os !== 'iOS') {
        return true
    } else {
        var platformIsOther = platform.indexOf('win') < 0 &&
            platform.indexOf('linux') < 0 &&
            platform.indexOf('mac') < 0 &&
            platform.indexOf('iphone') < 0 &&
            platform.indexOf('ipad') < 0
        if (platformIsOther !== (os === 'Other')) {
            return true
        }
    }

    return typeof navigator.plugins === 'undefined' && os !== 'Windows' && os !== 'Windows Phone'
}

var getHasLiedBrowser = function () {
    var userAgent = navigator.userAgent.toLowerCase()
    var productSub = navigator.productSub

    // we extract the browser from the user agent (respect the order of the tests)
    var browser
    if (userAgent.indexOf('firefox') >= 0) {
        browser = 'Firefox'
    } else if (userAgent.indexOf('opera') >= 0 || userAgent.indexOf('opr') >= 0) {
        browser = 'Opera'
    } else if (userAgent.indexOf('chrome') >= 0) {
        browser = 'Chrome'
    } else if (userAgent.indexOf('safari') >= 0) {
        browser = 'Safari'
    } else if (userAgent.indexOf('trident') >= 0) {
        browser = 'Internet Explorer'
    } else {
        browser = 'Other'
    }

    if ((browser === 'Chrome' || browser === 'Safari' || browser === 'Opera') && productSub !== '20030107') {
        return true
    }

    // eslint-disable-next-line no-eval
    var tempRes = eval.toString().length
    if (tempRes === 37 && browser !== 'Safari' && browser !== 'Firefox' && browser !== 'Other') {
        return true
    } else if (tempRes === 39 && browser !== 'Internet Explorer' && browser !== 'Other') {
        return true
    } else if (tempRes === 33 && browser !== 'Chrome' && browser !== 'Opera' && browser !== 'Other') {
        return true
    }

    // We create an error to see how it is handled
    var errFirefox
    try {
        // eslint-disable-next-line no-throw-literal
        throw 'a'
    } catch (err) {
        try {
            err.toSource()
            errFirefox = true
        } catch (errOfErr) {
            errFirefox = false
        }
    }
    return errFirefox && browser !== 'Firefox' && browser !== 'Other'
}

var getWebglCanvas = function () {
    var canvas = document.createElement('canvas')
    var gl = null
    try {
        gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    } catch (e) {
        /* squelch */ }
    if (!gl) {
        gl = null
    }
    return gl
}

var isCanvasSupported = function () {
    var elem = document.createElement('canvas')
    return !!(elem.getContext && elem.getContext('2d'))
}

var isWebGlSupported = function () {
    // code taken from Modernizr
    if (!isCanvasSupported()) {
        return false
    }

    var glContext = getWebglCanvas()
    return !!window.WebGLRenderingContext && !!glContext
}


/**
 * end copy from https://github.com/Valve/fingerprintjs2/blob/master/fingerprint2.js
 */


var hasLiedUserAgent = function () {
    var ua = window.navigator.userAgent
    if (ua == undefined || ua == '') {
        return true;
    }
    return false;
}

var hashLiedChrome = function () {
    if (/Chrome/.test(window.navigator.userAgent)) {
        if (!window.chrome || !window.chrome.runtime || !window.chrome.app || !window.chrome.csi || !window.chrome.loadTimes) {
            // headless...
            return true;
        }
    }
    return false;
}

var isWebDriver = function () {
    return !(navigator.webdriver == undefined);
}

var hasLiedStorage = function () {
    return !window.sessionStorage || !window.localStorage || !window.indexedDB;
}


var hasLiedPlugins = function () {
    return (!navigator.plugins || navigator.plugins.length == 0)

}

var hasLiedMimeTypes = function () {
    return navigator.mimeTypes.length == 0
}

var hasLiedWebGL = function () {
    var canvas = document.createElement('canvas');
    var gl = canvas.getContext('webgl');

    var debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    var vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
    var renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);

    return vendor == "Brian Paul" && renderer == "Mesa OffScreen";
}

// TODO test on failed img
// TODO test on css hairline
```