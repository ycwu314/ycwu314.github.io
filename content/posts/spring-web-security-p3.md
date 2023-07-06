---
title: spring security系列3：SecurityContext
date: 2020-08-21 16:09:48
tags: [spring, java]
categories: [spring]
keywords: [SecurityContext, SecurityContextPersistenceFilter]
description: SecurityContext是安全相关的上下文信息。
---

了解request的安全上下文信息。
<!-- more -->

# SecurityContext和SecurityContextHolder

SecurityContext抽象是当前线程执行所需要的最小安全信息，提供了Authentication对象入口。
```java
public interface SecurityContext extends Serializable {

	Authentication getAuthentication();

	void setAuthentication(Authentication authentication);
}
```

SecurityContext保存在SecurityContextHolder。
```java
public class SecurityContextHolder {
	public static final String MODE_THREADLOCAL = "MODE_THREADLOCAL";
	public static final String MODE_INHERITABLETHREADLOCAL = "MODE_INHERITABLETHREADLOCAL";
	public static final String MODE_GLOBAL = "MODE_GLOBAL";
	public static final String SYSTEM_PROPERTY = "spring.security.strategy";
	private static String strategyName = System.getProperty(SYSTEM_PROPERTY);
	private static SecurityContextHolderStrategy strategy;
	private static int initializeCount = 0;

	static {
		initialize();
	}
```
SecurityContextHolder核心是怎样存储SecurityContext。使用策略模式，交给SecurityContextHolderStrategy实现。

SecurityContextHolderStrategy有3种内置实现：
- ThreadLocalSecurityContextHolderStrategy
- GlobalSecurityContextHolderStrategy
- InheritableThreadLocalSecurityContextHolderStrategy

很自然的一个问题，SecurityContextHolder是怎么产生的？
答案是SecurityContextPersistenceFilter。

# SecurityContextPersistenceFilter

SecurityContextPersistenceFilter负责在request处理之前，填充SecurityContextHolder；处理request之后，清理SecurityContextHolder。
```java
public class SecurityContextPersistenceFilter extends GenericFilterBean {

	public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
			throws IOException, ServletException {
		HttpServletRequest request = (HttpServletRequest) req;
		HttpServletResponse response = (HttpServletResponse) res;

		if (request.getAttribute(FILTER_APPLIED) != null) {
			// ensure that filter is only applied once per request
			chain.doFilter(request, response);
			return;
		}

		final boolean debug = logger.isDebugEnabled();

		request.setAttribute(FILTER_APPLIED, Boolean.TRUE);

		if (forceEagerSessionCreation) {
			HttpSession session = request.getSession();

			if (debug && session.isNew()) {
				logger.debug("Eagerly created session: " + session.getId());
			}
		}

		HttpRequestResponseHolder holder = new HttpRequestResponseHolder(request,
				response);
		SecurityContext contextBeforeChainExecution = repo.loadContext(holder);

		try {
            // 在request处理之前填充SecurityContextHolder
			SecurityContextHolder.setContext(contextBeforeChainExecution);
            // 继续filter chain处理
			chain.doFilter(holder.getRequest(), holder.getResponse());

		}
		finally {
			SecurityContext contextAfterChainExecution = SecurityContextHolder
					.getContext();
			// Crucial removal of SecurityContextHolder contents - do this before anything
			// else.
            // request处理之后清理SecurityContextHolder
			SecurityContextHolder.clearContext();
			repo.saveContext(contextAfterChainExecution, holder.getRequest(),
					holder.getResponse());
			request.removeAttribute(FILTER_APPLIED);

			if (debug) {
				logger.debug("SecurityContextHolder now cleared, as request processing completed");
			}
		}
	}

}
```

# SecurityContextRepository

SecurityContextRepository负责抽象SecurityContext的存储。
主要实现是HttpSessionSecurityContextRepository。

```java
public SecurityContext loadContext(HttpRequestResponseHolder requestResponseHolder) {
	HttpServletRequest request = requestResponseHolder.getRequest();
	HttpServletResponse response = requestResponseHolder.getResponse();
	HttpSession httpSession = request.getSession(false);
	SecurityContext context = readSecurityContextFromSession(httpSession);

	if (context == null) {
		if (logger.isDebugEnabled()) {
			logger.debug("No SecurityContext was available from the HttpSession: "
					+ httpSession + ". " + "A new one will be created.");
		}
		context = generateNewContext();
	}

	SaveToSessionResponseWrapper wrappedResponse = new SaveToSessionResponseWrapper(
			response, request, httpSession != null, context);
	requestResponseHolder.setResponse(wrappedResponse);
	requestResponseHolder.setRequest(new SaveToSessionRequestWrapper(
			request, wrappedResponse));

	return context;
}
```

SaveToSessionResponseWrapper需要注意saveContext()，这里有些细节处理。
```java
protected void saveContext(SecurityContext context) {
	final Authentication authentication = context.getAuthentication();
	HttpSession httpSession = request.getSession(false);

	// See SEC-776
	if (authentication == null || trustResolver.isAnonymous(authentication)) {
		if (logger.isDebugEnabled()) {
			logger.debug("SecurityContext is empty or contents are anonymous - context will not be stored in HttpSession.");
		}
		if (httpSession != null && authBeforeExecution != null) {
			// SEC-1587 A non-anonymous context may still be in the session
			// SEC-1735 remove if the contextBeforeExecution was not anonymous
			httpSession.removeAttribute(springSecurityContextKey);
		}
		return;
	}

	if (httpSession == null) {
		httpSession = createNewSessionIfAllowed(context);
	}
    
	// If HttpSession exists, store current SecurityContext but only if it has
	// actually changed in this thread (see SEC-37, SEC-1307, SEC-1528)
	if (httpSession != null) {
		// We may have a new session, so check also whether the context attribute
		// is set SEC-1561
		if (contextChanged(context)
				|| httpSession.getAttribute(springSecurityContextKey) == null) {
			httpSession.setAttribute(springSecurityContextKey, context);
			if (logger.isDebugEnabled()) {
				logger.debug("SecurityContext '" + context
						+ "' stored to HttpSession: '" + httpSession);
			}
		}
	}
}
```

# SecurityContextConfigurer

和SecurityContext相关的配置，都由SecurityContextConfigurer处理。
```java
public final class SecurityContextConfigurer<H extends HttpSecurityBuilder<H>> extends
		AbstractHttpConfigurer<SecurityContextConfigurer<H>, H> {

	public void configure(H http) {

		SecurityContextRepository securityContextRepository = http
				.getSharedObject(SecurityContextRepository.class);
		if (securityContextRepository == null) {
			securityContextRepository = new HttpSessionSecurityContextRepository();
		}
		SecurityContextPersistenceFilter securityContextFilter = new SecurityContextPersistenceFilter(
				securityContextRepository);
		SessionManagementConfigurer<?> sessionManagement = http
				.getConfigurer(SessionManagementConfigurer.class);
		SessionCreationPolicy sessionCreationPolicy = sessionManagement == null ? null
				: sessionManagement.getSessionCreationPolicy();
		if (SessionCreationPolicy.ALWAYS == sessionCreationPolicy) {
			securityContextFilter.setForceEagerSessionCreation(true);
		}
		securityContextFilter = postProcess(securityContextFilter);
		http.addFilter(securityContextFilter);
	}

}
```
