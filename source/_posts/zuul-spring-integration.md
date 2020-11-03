---
title: zuul和spring集成分析
date: 2020-08-25 17:11:51
tags: [zuul, spring, java]
categories: [zuul]
keywords: [zuulServletFilter, zuulServlet]
description:
---
zuul和spring集成分析。
<!-- more -->

# zuul和spring集成

>Zuul is implemented as a Servlet. For the general cases, Zuul is embedded into the Spring Dispatch mechanism. 
>This lets Spring MVC be in control of the routing. In this case, Zuul buffers requests. 
>If there is a need to go through Zuul without buffering requests (for example, for large file uploads), the Servlet is also installed outside of the Spring Dispatcher. 
>By default, the servlet has an address of /zuul. This path can be changed with the zuul.servlet-path property.

zuul以servlet形式设计，集成到spring的DispatchServlet。

通过handler mapping形式，DispatchServlet把请求分发到zuul处理，依赖handler mapping。
```java
protected void initStrategies(ApplicationContext context) {
	initMultipartResolver(context);
	initLocaleResolver(context);
	initThemeResolver(context);
    // handler映射
	initHandlerMappings(context);
	initHandlerAdapters(context);
	initHandlerExceptionResolvers(context);
	initRequestToViewNameTranslator(context);
	initViewResolvers(context);
	initFlashMapManager(context);
}
```

{% asset_img zuul-handler-mappings.png %}

>对于大文件上传这种服务，如果经过DispatcherServlet，会影响性能。因为DispatcherServlet为了方便后续处理流程使用，会将multipart/form请求根据RFC1867规则进行统一分析处理，并且返回MultipartHttpServletRequest实例，通过它可以获取file和其他参数。

网关通常来说不需要获取MultipartHttpServletRequest，特别是大文件，这样会比较影响性能，可以直接用ZuulServlet处理，参见`ZuulServerAutoConfiguration`：
```java
@Bean
@ConditionalOnMissingBean(name = "zuulServlet")
@ConditionalOnProperty(name = "zuul.use-filter", havingValue = "false",
		matchIfMissing = true)
public ServletRegistrationBean zuulServlet() {
	ServletRegistrationBean<ZuulServlet> servlet = new ServletRegistrationBean<>(
			new ZuulServlet(), this.zuulProperties.getServletPattern());
	// The whole point of exposing this servlet is to provide a route that doesn't
	// buffer requests.
	servlet.addInitParameter("buffer-requests", "false");
	return servlet;
}

@Bean
@ConditionalOnMissingBean(name = "zuulServletFilter")
@ConditionalOnProperty(name = "zuul.use-filter", havingValue = "true",
		matchIfMissing = false)
public FilterRegistrationBean zuulServletFilter() {
	final FilterRegistrationBean<ZuulServletFilter> filterRegistration = new FilterRegistrationBean<>();
    // zuul.servletPath
	filterRegistration.setUrlPatterns(
			Collections.singleton(this.zuulProperties.getServletPattern()));
	filterRegistration.setFilter(new ZuulServletFilter());
    // 优先级最低哦
	filterRegistration.setOrder(Ordered.LOWEST_PRECEDENCE);
	// The whole point of exposing this servlet is to provide a route that doesn't
	// buffer requests.
	filterRegistration.addInitParameter("buffer-requests", "false");
	return filterRegistration;
}
```

`zuul.use-filter`是控制和spring整合的方式：
- true： **默认配置**，使用zuulServletFilter，先创建为FilterRegistrationBean，再注册到spring容器
- false：使用zuulServlet，先创建为ServletRegistrationBean，再注册到servlet容器

值得留意的是`buffer-requests`。
不管是ZuulServletFilter还是ZuulServlet，都由ZuulRunner对请求初始化。
bufferRequests决定是否包装request对象。
```java
/**
 *
 * @param bufferRequests - whether to wrap the ServletRequest in HttpServletRequestWrapper and buffer the body.
 */
public ZuulRunner(boolean bufferRequests) {
    this.bufferRequests = bufferRequests;
}

public void init(HttpServletRequest servletRequest, HttpServletResponse servletResponse) {
    RequestContext ctx = RequestContext.getCurrentContext();
    if (bufferRequests) {
        ctx.setRequest(new HttpServletRequestWrapper(servletRequest));
    } else {
        ctx.setRequest(servletRequest);
    }
    ctx.setResponse(new HttpServletResponseWrapper(servletResponse));
}
```

前面讲到大文件请求不应该包装。FormBodyWrapperFilter不对form和multipart包装：
- application/x-www-form-urlencoded
- multipart/form-data

```java
public boolean shouldFilter() {
	RequestContext ctx = RequestContext.getCurrentContext();
	HttpServletRequest request = ctx.getRequest();
	String contentType = request.getContentType();
	// Don't use this filter on GET method
	if (contentType == null) {
		return false;
	}
	// Only use this filter for form data and only for multipart data in a
	// DispatcherServlet handler
	try {
		MediaType mediaType = MediaType.valueOf(contentType);
		return MediaType.APPLICATION_FORM_URLENCODED.includes(mediaType)
				|| (isDispatcherServletRequest(request)
						&& MediaType.MULTIPART_FORM_DATA.includes(mediaType));
	}
	catch (InvalidMediaTypeException ex) {
		return false;
	}
}
```

画了一张图，整理上面核心类的关系和流程：
{% asset_img arch.png %}

# zuul本地路由

把流量转发到本地zuul自定义的controller处理。使用`forward`路由：
```yaml
zuul:
  sensitive-headers:
  routes:
    # 本地路由
    login-service:
      path: /rest_login/**
      url: forward:/rest_login
```
