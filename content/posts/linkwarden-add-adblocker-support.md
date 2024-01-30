---
title: "Linkwarden 添加 Adblocker 支持"
date: 2024-01-30T17:11:39+08:00
tags: ["self-hosted"]
categories: ["self-hosted"]
description: 美化 linkwarden 网页抓取。
---

尽管在chrome安装了adblock plus、circle阅读器插件，但是抓取网页不理想。

研究了源码：

https://github.com/linkwarden/linkwarden/blob/047e156cfbe9a0794287ebac1768e1677470f94c/lib/api/archiveHandler.ts#L115


```typescript
// Readability
const content = await page.content();

const window = new JSDOM("").window;
const purify = DOMPurify(window);
const cleanedUpContent = purify.sanitize(content);
const dom = new JSDOM(cleanedUpContent, { url: link.url || "" });
const article = new Readability(dom.window.document).parse();
const articleText = article?.textContent
  .replace(/ +(?= )/g, "") // strip out multiple spaces
  .replace(/(\r\n|\n|\r)/gm, " "); // strip out line breaks
```

1. DOMPurify 处理xss攻击
2. 把页面内容丢到虚拟dom
3. 使用Mozilla阅读器插件提取内容

关键要过滤原来页面dom。
显然调用远程chrome浏览器的adp、circle阅读器并没有生效。

于是考虑在playwright直接使用adp插件来实现。找到 adblocker 这个插件：[adblocker-playwright-example](https://github.com/ghostery/adblocker/blob/master/packages/adblocker-playwright-example/index.ts)


1. 在容器内安装插件
```bash
npm install --save @cliqz/adblocker-playwright
```

2. 修改`archiveHandler.ts`
```typescript
export default async function archiveHandler(link: LinksAndCollectionAndOwner) {

  const myFullList = [...fullLists,
    `https://raw.githubusercontent.com/xxx/adp-rules/main/my-adp-rules.txt`,
  ];


  const blocker = await PlaywrightBlocker.fromLists(fetch, myFullList, {
      enableCompression: true,
  });

  // const browser = await chromium.launch();
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = await browser.newContext(devices["Desktop Chrome"]);
  const page = await context.newPage();

  await blocker.enableBlockingInPage(page);
```

adblocker 插件内置一些过滤规则。再把自定义网站规则也加上去。

顺利过滤页面上多余元素。


为了新建容器时候能生效：
```bash
docker compose up -d
sleep 15
docker exec -it linkwarden-linkwarden-1 /bin/bash -c "npm install --save @cliqz/adblocker-playwright"
docker restart linkwarden-linkwarden-1
```