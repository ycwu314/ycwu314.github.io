---
title: spring security系列5：CORS
date: 2020-08-25 15:40:25
tags: [spring, java]
categories: [spring]
keywords: []
description:
---
{% asset_img slug [title] %}
<!-- more -->

# CorsConfiguration

CorsConfiguration是配置类。
值得注意的是`checkOrigin`方法：
```java
public String checkOrigin(@Nullable String requestOrigin) {
	if (!StringUtils.hasText(requestOrigin)) {
		return null;
	}
	if (ObjectUtils.isEmpty(this.allowedOrigins)) {
		return null;
	}
	if (this.allowedOrigins.contains(ALL)) {
		if (this.allowCredentials != Boolean.TRUE) {
			return ALL;
		}
		else {
			return requestOrigin;
		}
	}
	for (String allowedOrigin : this.allowedOrigins) {
		if (requestOrigin.equalsIgnoreCase(allowedOrigin)) {
			return requestOrigin;
		}
	}
	return null;
}
```

当允许的Origin为`*`，且credentials为`true`，则返回当前请求的Origin、而不是`*`。


# CorsFilter

CorsProcessor是CORS处理器抽象，DefaultCorsProcessor。
CorsFilter是CORS的过滤器，调用CorsProcessor进行实际操作。

```java
protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
		FilterChain filterChain) throws ServletException, IOException {
	CorsConfiguration corsConfiguration = this.configSource.getCorsConfiguration(request);
	boolean isValid = this.processor.processRequest(corsConfiguration, request, response);
	if (!isValid || CorsUtils.isPreFlightRequest(request)) {
		return;
	}
	filterChain.doFilter(request, response);
}
```

在w3c标准中，浏览器对复杂跨域请求，首先发送options请求判断能否执行。
对应的是`CorsUtils#isPreFlightRequest()`

```java
public static boolean isPreFlightRequest(HttpServletRequest request) {
	return (HttpMethod.OPTIONS.matches(request.getMethod()) &&
			request.getHeader(HttpHeaders.ORIGIN) != null &&
			request.getHeader(HttpHeaders.ACCESS_CONTROL_REQUEST_METHOD) != null);
}
```

FilterComparator定义了filter顺序。
```java
final class FilterComparator implements Comparator<Filter>, Serializable {
	private static final int INITIAL_ORDER = 100;
	private static final int ORDER_STEP = 100;
	private final Map<String, Integer> filterToOrder = new HashMap<>();

	FilterComparator() {
		Step order = new Step(INITIAL_ORDER, ORDER_STEP);
		put(ChannelProcessingFilter.class, order.next());
		put(ConcurrentSessionFilter.class, order.next());
		put(WebAsyncManagerIntegrationFilter.class, order.next());
		put(SecurityContextPersistenceFilter.class, order.next());
		put(HeaderWriterFilter.class, order.next());
        // CORS filter here
		put(CorsFilter.class, order.next());
		put(CsrfFilter.class, order.next());
		put(LogoutFilter.class, order.next());
        // more codes
```