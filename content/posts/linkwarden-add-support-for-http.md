---
title: "Linkwarden 添加 Http 网页支持"
date: 2024-01-29T15:37:07+08:00
tags: ["self-hosted"]
categories: ["self-hosted"]
description: 原生 Linkwarden 不支持 http。
---

向 Linkwarden 添加链接，一直没有抓取成果。
查看docker日志：

```log
[1] Processing link http://xxx/f/xxx.html for user 1
[1] TypeError [ERR_INVALID_PROTOCOL]: Protocol "http:" not supported. Expected "https:"
[1]     at new NodeError (node:internal/errors:405:5)
[1]     at new ClientRequest (node:_http_client:188:11)
[1]     at request (node:http:100:10)
[1]     at /data/node_modules/node-fetch/lib/index.js:1482:15
[1]     at new Promise (<anonymous>)
[1]     at fetch (/data/node_modules/node-fetch/lib/index.js:1451:9)
[1]     at validateUrlSize (/data/lib/api/validateUrlSize.ts:11:33)
[1]     at /data/lib/api/archiveHandler.ts:44:34
[1]     at archiveHandler (/data/lib/api/archiveHandler.ts:272:9)
[1]     at async archiveLink (/data/scripts/worker.ts:145:7) {
[1]   code: 'ERR_INVALID_PROTOCOL'

```

继续打开[validateUrlSize](https://github.com/linkwarden/linkwarden/blob/047e156cfbe9a0794287ebac1768e1677470f94c/lib/api/validateUrlSize.ts#L4)的实现：

```typescript
export default async function validateUrlSize(url: string) {
  try {
    const httpsAgent = new https.Agent({
      rejectUnauthorized:
        process.env.IGNORE_UNAUTHORIZED_CA === "true" ? false : true,
    });

    const response = await fetch(url, {
      method: "HEAD",
      agent: httpsAgent,
    });
```

这里只用https，遇到http的链接当然报错。

解决方法：
- 添加一个反向代理，把http链接转换成https
- 或者，修改源码，添加http支持

选择后者。

```typescript
import fetch from "node-fetch";
import http from "http";
import https from "https";

export default async function validateUrlSize(url: string) {
  try {
    const protocol = new URL(url).protocol;

    let agent;
    if (protocol === "https:") {
      agent = new https.Agent({
        rejectUnauthorized:
          process.env.IGNORE_UNAUTHORIZED_CA === "true" ? false : true,
      });
    } else {
      agent = new http.Agent();
    }

    const response = await fetch(url, {
      method: "HEAD",
      agent: agent,
    });

```

然后docker compose启动时候覆盖
```yml
services:
  linkwarden:
    deploy:
        resources:
            limits:
              cpus: "0.50"
    env_file: .env
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/postgres
    restart: always
    image: ghcr.io/linkwarden/linkwarden:v2.4.9
    volumes:
      - /root/vps_setup/linkwarden/archiveHandler.ts:/data/lib/api/archiveHandler.ts
      - /root/vps_setup/linkwarden/validateUrlSize.ts:/data/lib/api/validateUrlSize.ts
```