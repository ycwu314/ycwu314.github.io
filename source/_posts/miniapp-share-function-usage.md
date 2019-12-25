---
title: 小程序分享功能简单使用
date: 2019-12-25 11:21:30
tags: [小程序]
categories: [小程序]
keywords: [小程序 分享]
description: onShareAppMessage开启分享功能。在onLoad中接收分享参数。小程序已经关闭分享监听。
---

# 开启分享功能

page中增加`onShareAppMessage()`就可以开启分享功能。
<!-- more -->
```js
/**
   * 用户点击右上角分享
   */
onShareAppMessage: function () {  
  var that = this
  var playIndex = this.data.playIndex

  return {
    imageUrlId: SHARE_MSG_IMG_ID, // 通过 MP 系统审核的图片编号
    imageUrl: SHARE_MSG_IMG_URL,   // 通过 MP 系统审核的图片地址
    path: '/pages/index/index?uid=' + that.data.musicList[playIndex]['uid']
  }
}
```

注意：imageUrl尺寸长宽比例是`5:4`。

`path`是要分享的页面，必须是全路径。
url后面可以增加自定义参数。

# 读取分享参数

我的场景很简单，只要读取分享url参数即可。
`onLoad()`增加options参数就可以了。
```js
onLoad: function (options) {
  if (options && options.uid) {
    console.log('share uid=', options.uid)
    this.data.fromUid = options.uid
  }
```

# 回调问题

最初为了调试，增加分享成功的回调，发现模拟器和真机都不生效。
后来发现微信把分享回调能力关闭了，具体参见这个公告：[“分享监听”能力调整](https://developers.weixin.qq.com/community/develop/doc/0000447a5b431807af57249a551408)。



