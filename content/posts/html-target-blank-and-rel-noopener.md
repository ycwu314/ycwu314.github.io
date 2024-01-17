---
title: "html中的 target=_blank 和 rel=noopener"
date: 2024-01-17T10:40:02+08:00
tags: ["html"]
categories: ["html"]
description: 温故知新。
---

在 HTML 中，target 属性用于指定链接的打开方式，即链接在何处显示。它可以用在 `<a>`（锚元素）、`<form>`（表单元素）等标签上。

```html
<a target="_blank|_self|_parent|_top|framename">
```

取值范围：

| Value    | Description                                                 |
|----------|-------------------------------------------------------------|
| `_blank` | Opens the linked document in a new window or tab            |
| `_self`  | Opens the linked document in the same frame as it was clicked (this is default) |
| `_parent`| Opens the linked document in the parent frame               |
| `_top`   | Opens the linked document in the full body of the window    |
| `framename` | Opens the linked document in the named iframe              |

关于这些选项，stack上有篇详细讨论：
[Difference between _self, _top, and _parent in the anchor tag target attribute](https://stackoverflow.com/questions/18470097/difference-between-self-top-and-parent-in-the-anchor-tag-target-attribute)

这里记住`_self`是默认值、`_blank`会打开新窗口（常用选项）即可。

每个window都有一个关联的opener对象。针对`target="_blank"`，默认的opener对象为打开改链接的原始窗口，这可能导致opener攻击。
（but觉得实施条件有点苛刻）

为了防止这种攻击，可以使用 `rel="noopener"` 或 `rel="noopener noreferrer"`。noopener 阻止新窗口访问原始窗口的 window.opener 对象，从而减少了攻击者能够滥用的可能性。


现代浏览器，已经做了安全升级，对`target=_blank`，默认开启`rel=noopener`。参见：
- [About rel=noopener](https://mathiasbynens.github.io/rel-noopener/)。这篇文章做了交互链接，可以检查浏览器是否支持这个特性。
- [Windows opened via `<a target=_blank>` should not have an opener by default]https://github.com/whatwg/html/issues/4078



