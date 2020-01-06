---
title: HttpURLConnection disconnect
date: 2020-01-06 14:32:51
tags: [java, nacos, http]
categories: [java]
keywords: [HttpURLConnection disconnect]
description: HttpURLConnection.disconnect() 会关闭底层连接。如果要复用连接，使用 HttpURLConnection.getInputSteam().close()。
---

# 背景

在看nacos client的代码，发现网络相关http实现是包装HttpURLConnection，其中关闭连接是：
```java
finally {
    if (null != conn) {
        conn.disconnect();
    }
}
```
<!-- more -->

很少直接用HttpURLConnection写代码了，但是记得之前写代码，通常只关闭流
```java
finally {
    if (null != conn && conn.getInputSteam()!= null ) {
        conn.getInputSteam().close();
    }
}
```
于是复习下。

# HttpURLConnection.disconnect()

HttpURLConnection对disconnect描述；
```java
    /**
     * Indicates that other requests to the server
     * are unlikely in the near future. Calling disconnect()
     * should not imply that this HttpURLConnection
     * instance can be reused for other requests.
     */
    public abstract void disconnect();
```

具体实现类：`sun.net.www.protocol.http.HttpURLConnection`
```java
    public void disconnect() {
        this.responseCode = -1;
        if (this.pi != null) {
            this.pi.finishTracking();
            this.pi = null;
        }

        if (this.http != null) {
            if (this.inputStream != null) {
                HttpClient var1 = this.http;
                boolean var2 = var1.isKeepingAlive();

                try {
                    this.inputStream.close();
                } catch (IOException var4) {
                }

                if (var2) {
                    var1.closeIdleConnection();
                }
            } else {
                this.http.setDoNotRetry(true);
                this.http.closeServer();
            }

            this.http = null;
            this.connected = false;
        }

        this.cachedInputStream = null;
        if (this.cachedHeaders != null) {
            this.cachedHeaders.reset();
        }

    }
```

`sun.net.www.http.HttpClient`
```java

    protected static KeepAliveCache kac = new KeepAliveCache();

    public void closeIdleConnection() {
        HttpClient var1 = kac.get(this.url, (Object)null);
        if (var1 != null) {
            var1.closeServer();
        }

    }

    public void closeServer() {
        try {
            this.keepingAlive = false;
            this.serverSocket.close();
        } catch (Exception var2) {
        }

    }    
```

小结：disconnect()清除keepingAlive，关闭serverSocket。

# HttpURLConnection.getInputSteam().close()

HttpURLConnection的javadoc
> * Calling the close() methods
> * on the InputStream or OutputStream of an HttpURLConnection
> * after a request may free network resources associated with this
> * instance but has no effect on any shared persistent connection.
> * Calling the disconnect() method may close the underlying socket
> * if a persistent connection is otherwise idle at that time.

# 小结

在开启keep-alive的情况下：
- `HttpURLConnection.disconnect()`会关闭底层socket。
- `HttpURLConnection.getInputSteam().close()`只关闭输入流，可以重用底层socket。

nacos client定时向nacos server轮询配置更新，查询结束主动关闭连接， 不复用底层socket，问题也不大。

# 资料

- [Safe use of HttpURLConnection](https://stackoverflow.com/questions/4767553/safe-use-of-httpurlconnection)
- [http-keepalive](http://docs.oracle.com/javase/6/docs/technotes/guides/net/http-keepalive.html)