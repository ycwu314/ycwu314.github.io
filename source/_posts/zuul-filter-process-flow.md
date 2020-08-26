---
title: zuul filter处理流程
date: 2020-08-25 19:56:34
tags: [zuul, spring, java]
categories: [zuul]
keywords: [sendZuulResponse, FilterProcessor, SendResponseFilter, RibbonRoutingFilter, PreDecorationFilter]
description:
---

顺便看下zuul filter的处理流程。

<!-- more -->

# ZuulServlet和ZuulServletFilter

{% asset_img arch.png %}

ZuulServlet和ZuulServletFilter的处理逻辑是相似的。

`ZuulServlet#service()`：
```java
    public void service(javax.servlet.ServletRequest servletRequest, javax.servlet.ServletResponse servletResponse) throws ServletException, IOException {
        try {
            init((HttpServletRequest) servletRequest, (HttpServletResponse) servletResponse);

            // Marks this request as having passed through the "Zuul engine", as opposed to servlets
            // explicitly bound in web.xml, for which requests will not have the same data attached
            RequestContext context = RequestContext.getCurrentContext();
            context.setZuulEngineRan();

            try {
                preRoute();
            } catch (ZuulException e) {
                error(e);
                postRoute();
                return;
            }
            try {
                route();
            } catch (ZuulException e) {
                error(e);
                postRoute();
                return;
            }
            try {
                postRoute();
            } catch (ZuulException e) {
                error(e);
                return;
            }

        } catch (Throwable e) {
            error(new ZuulException(e, 500, "UNHANDLED_EXCEPTION_" + e.getClass().getName()));
        } finally {
            RequestContext.getCurrentContext().unset();
        }
    }
```


`ZuulServletFilter#doFilter()`：
```java
    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain) throws IOException, ServletException {
        try {
            init((HttpServletRequest) servletRequest, (HttpServletResponse) servletResponse);
            try {
                preRouting();
            } catch (ZuulException e) {
                error(e);
                postRouting();
                return;
            }
            
            // Only forward onto to the chain if a zuul response is not being sent
            if (!RequestContext.getCurrentContext().sendZuulResponse()) {
                filterChain.doFilter(servletRequest, servletResponse);
                return;
            }
            
            try {
                routing();
            } catch (ZuulException e) {
                error(e);
                postRouting();
                return;
            }
            try {
                postRouting();
            } catch (ZuulException e) {
                error(e);
                return;
            }
        } catch (Throwable e) {
            error(new ZuulException(e, 500, "UNCAUGHT_EXCEPTION_FROM_FILTER_" + e.getClass().getName()));
        } finally {
            RequestContext.getCurrentContext().unset();
        }
    }
```

当zuul以filter方式使用，则增加了`sendZuulResponse`处理逻辑。
这样请求直接在zuul server处理完成，不会透传到后端服务。

注意，即使设置了sendZuulResponse，也要处理完当前后续filter chain：
```java
// Only forward onto to the chain if a zuul response is not being sent
if (!RequestContext.getCurrentContext().sendZuulResponse()) {
    filterChain.doFilter(servletRequest, servletResponse);
    return;
}
```


preRouting、routing、postRouting、error是zuul filter的核心流程。
都是调用`FilterProcessor#runFilters()`。
sType对应了定义ZuulFilter的`filterType`。
```java
    public Object runFilters(String sType) throws Throwable {
        if (RequestContext.getCurrentContext().debugRouting()) {
            Debug.addRoutingDebug("Invoking {" + sType + "} type filters");
        }
        boolean bResult = false;
        List<ZuulFilter> list = FilterLoader.getInstance().getFiltersByType(sType);
        if (list != null) {
            for (int i = 0; i < list.size(); i++) {
                ZuulFilter zuulFilter = list.get(i);
                Object result = processZuulFilter(zuulFilter);
                if (result != null && result instanceof Boolean) {
                    bResult |= ((Boolean) result);
                }
            }
        }
        return bResult;
    }
```

`FilterProcessor#processZuulFilter()`执行filter方法，并且添加统计metrics。
```java
// more code
ZuulFilterResult result = filter.runFilter();
ExecutionStatus s = result.getStatus();
// more code
```

`ZuulFilter#runFilter()`，熟悉的template模式：
```java
    public ZuulFilterResult runFilter() {
        // 初始化结果为 ExecutionStatus.DISABLED
        ZuulFilterResult zr = new ZuulFilterResult();
        if (!isFilterDisabled()) {
            if (shouldFilter()) {
                Tracer t = TracerFactory.instance().startMicroTracer("ZUUL::" + this.getClass().getSimpleName());
                try {
                    // 子类实现run方法
                    Object res = run();
                    zr = new ZuulFilterResult(res, ExecutionStatus.SUCCESS);
                } catch (Throwable e) {
                    t.setName("ZUUL::" + this.getClass().getSimpleName() + " failed");
                    zr = new ZuulFilterResult(ExecutionStatus.FAILED);
                    zr.setException(e);
                } finally {
                    t.stopAndLog();
                }
            } else {
                zr = new ZuulFilterResult(ExecutionStatus.SKIPPED);
            }
        }
        return zr;
    }
```

# ZuulFilter

zuul 1 
{% asset_img zuul-1-flow.png %}

zuul 2
{% asset_img zuul-2-flow.png %}

默认zuul filter顺序如下，图片来自网上
{% asset_img zuul-filter-order.png %}

## ServletDetectionFilter

用来检测当前请求是通过Spring的DispatcherServlet处理运行的，还是通过Zuu1Servlet来处理运行的
```java
	public Object run() {
		RequestContext ctx = RequestContext.getCurrentContext();
		HttpServletRequest request = ctx.getRequest();
		if (!(request instanceof HttpServletRequestWrapper)
				&& isDispatcherServletRequest(request)) {
			ctx.set(IS_DISPATCHER_SERVLET_REQUEST_KEY, true);
		}
		else {
			ctx.set(IS_DISPATCHER_SERVLET_REQUEST_KEY, false);
		}

		return null;
	}

	private boolean isDispatcherServletRequest(HttpServletRequest request) {
		return request.getAttribute(
				DispatcherServlet.WEB_APPLICATION_CONTEXT_ATTRIBUTE) != null;
	}
```

像上传文件之类的操作，可以直接交给ZuulServlet处理。相关的filter还有FormBodyWrapperFilter。

## PreDecorationFilter

转发前的前置处理，根据RouteLocator获取路由类型，再向RequestContext填充辅助标记。
zuul支持以下类型：
- http、https
- forward
- serviceId

工作流程：
1. 如果找不到路由，则设置为forward类型
2. 找到路由，则：
- 过滤敏感header
- 判断请求能否重试
- 如果是http、https请求，就设置host和origin
- 如果是forward类型，就设置规范化的`forward.to`标记
- 否则，是serviceId类型
- 如果是proxy请求，增加x-forwarded-for、remote-addr字段


```java
public Object run() {
	RequestContext ctx = RequestContext.getCurrentContext();
	final String requestURI = this.urlPathHelper
			.getPathWithinApplication(ctx.getRequest());
	Route route = this.routeLocator.getMatchingRoute(requestURI);
	if (route != null) {
		String location = route.getLocation();
		if (location != null) {
			ctx.put(REQUEST_URI_KEY, route.getPath());
			ctx.put(PROXY_KEY, route.getId());
			if (!route.isCustomSensitiveHeaders()) {
				this.proxyRequestHelper.addIgnoredHeaders(
						this.properties.getSensitiveHeaders().toArray(new String[0]));
			}
			else {
				this.proxyRequestHelper.addIgnoredHeaders(
						route.getSensitiveHeaders().toArray(new String[0]));
			}
			if (route.getRetryable() != null) {
				ctx.put(RETRYABLE_KEY, route.getRetryable());
			}
			if (location.startsWith(HTTP_SCHEME + ":")
					|| location.startsWith(HTTPS_SCHEME + ":")) {
				ctx.setRouteHost(getUrl(location));
				ctx.addOriginResponseHeader(SERVICE_HEADER, location);
			}
			else if (location.startsWith(FORWARD_LOCATION_PREFIX)) {
				ctx.set(FORWARD_TO_KEY,
						StringUtils.cleanPath(
								location.substring(FORWARD_LOCATION_PREFIX.length())
										+ route.getPath()));
				ctx.setRouteHost(null);
				return null;
			}
			else {
				// set serviceId for use in filters.route.RibbonRequest
				ctx.set(SERVICE_ID_KEY, location);
				ctx.setRouteHost(null);
				ctx.addOriginResponseHeader(SERVICE_ID_HEADER, location);
			}
			if (this.properties.isAddProxyHeaders()) {
				addProxyHeaders(ctx, route);
				String xforwardedfor = ctx.getRequest()
						.getHeader(X_FORWARDED_FOR_HEADER);
				String remoteAddr = ctx.getRequest().getRemoteAddr();
				if (xforwardedfor == null) {
					xforwardedfor = remoteAddr;
				}
				else if (!xforwardedfor.contains(remoteAddr)) { // Prevent duplicates
					xforwardedfor += ", " + remoteAddr;
				}
				ctx.addZuulRequestHeader(X_FORWARDED_FOR_HEADER, xforwardedfor);
			}
			if (this.properties.isAddHostHeader()) {
				ctx.addZuulRequestHeader(HttpHeaders.HOST,
						toHostHeader(ctx.getRequest()));
			}
		}
	}
	else {
		log.warn("No route found for uri: " + requestURI);
		String forwardURI = getForwardUri(requestURI);
		ctx.set(FORWARD_TO_KEY, forwardURI);
	}
	return null;
}

```

对于forward，通过url中使用forward来指定需要跳转的服务器资源路径（跳转到网关层）。
来自官网的例子：
```yaml
 zuul:
  routes:
    first:
      path: /first/**
      url: http://first.example.com
    second:
      path: /second/**
      url: forward:/second
    third:
      path: /third/**
      url: forward:/3rd
    legacy:
      path: /**
      url: http://legacy.example.com
```
则`/second/**`和`/third/**`跳转到网关层处理。


## RibbonRoutingFilter

只处理serviceId转发，底层使用ribbon、hystrix和可配置的http客户端发送请求。

其中使用工厂模式，RibbonCommandFactory支持okhttp、httpclient、restclient等http客户端。

## SimpleHostRoutingFilter

只处理具体的url转发，即RequestContext指定了route host。

## SendForwardFilter

只处理forward请求。使用了servlet规范的RequestDispatcher实现转发。

```java
public Object run() {
	try {
		RequestContext ctx = RequestContext.getCurrentContext();
		String path = (String) ctx.get(FORWARD_TO_KEY);
		RequestDispatcher dispatcher = ctx.getRequest().getRequestDispatcher(path);
		if (dispatcher != null) {
            // 已经转发过的标记
			ctx.set(SEND_FORWARD_FILTER_RAN, true);
			if (!ctx.getResponse().isCommitted()) {
				dispatcher.forward(ctx.getRequest(), ctx.getResponse());
				ctx.getResponse().flushBuffer();
			}
		}
	}
	catch (Exception ex) {
		ReflectionUtils.rethrowRuntimeException(ex);
	}
	return null;
}
```


## SendErrorFilter

处理异常。把异常转发到网关处理（又是RequestDispatcher）。

```java
public Object run() {
	try {
		RequestContext ctx = RequestContext.getCurrentContext();
		ExceptionHolder exception = findZuulException(ctx.getThrowable());
		HttpServletRequest request = ctx.getRequest();
		request.setAttribute("javax.servlet.error.status_code",
				exception.getStatusCode());
		log.warn("Error during filtering", exception.getThrowable());
		request.setAttribute("javax.servlet.error.exception",
				exception.getThrowable());
		if (StringUtils.hasText(exception.getErrorCause())) {
			request.setAttribute("javax.servlet.error.message",
					exception.getErrorCause());
		}
        // RequestDispatcher是servlet规范定义的
		RequestDispatcher dispatcher = request.getRequestDispatcher(this.errorPath);
		if (dispatcher != null) {
			ctx.set(SEND_ERROR_FILTER_RAN, true);
			if (!ctx.getResponse().isCommitted()) {
				ctx.setResponseStatusCode(exception.getStatusCode());
                // 转发到网关层处理
				dispatcher.forward(request, ctx.getResponse());
			}
		}
	}
	catch (Exception ex) {
		ReflectionUtils.rethrowRuntimeException(ex);
	}
	return null;
}
```

## SendResponseFilter

该过滤器会检查请求上下文中是否包含请求响应相关的头信息、响应数据流或是响应体，只要包含其中一个的时候执行处理逻辑。
```java
public boolean shouldFilter() {
	RequestContext context = RequestContext.getCurrentContext();
	return context.getThrowable() == null
			&& (!context.getZuulResponseHeaders().isEmpty()
					|| context.getResponseDataStream() != null
					|| context.getResponseBody() != null);
}
```

