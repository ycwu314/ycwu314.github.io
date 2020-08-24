---
title: spring security系列4：Authentication相关
date: 2020-08-21 16:25:51
tags: [spring, java]
categories: [spring]
keywords: [AuthenticationEntryPoint, ExceptionTranslationFilter, AuthenticationManager, AbstractAuthenticationProcessingFilter]
description:
---

AuthenticationEntryPoint是不同类型验证方式的抽象入口。
ExceptionTranslationFilter根据AuthenticationException或者AccessDeniedException触发登录流程。
AbstractAuthenticationProcessingFilter和它的子类处理登录请求。
AuthenticationProvider用于处理Authentication请求，ProviderManager是其中一个实现。
<!-- more -->

# AuthenticationEntryPoint和ExceptionTranslationFilter

{% asset_img arch.png %}

AuthenticationEntryPoint是触发认证请求的入口，由ExceptionTranslationFilter使用。

ExceptionTranslationFilter会对
- AuthenticationException，没有验证
- AccessDeniedException，没有访问权限

开始验证流程。

```java
	private void handleSpringSecurityException(HttpServletRequest request,
			HttpServletResponse response, FilterChain chain, RuntimeException exception)
			throws IOException, ServletException {
		if (exception instanceof AuthenticationException) {
			logger.debug(
					"Authentication exception occurred; redirecting to authentication entry point",
					exception);

			sendStartAuthentication(request, response, chain,
					(AuthenticationException) exception);
		}
		else if (exception instanceof AccessDeniedException) {
			Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
			if (authenticationTrustResolver.isAnonymous(authentication) || authenticationTrustResolver.isRememberMe(authentication)) {
				logger.debug(
						"Access is denied (user is " + (authenticationTrustResolver.isAnonymous(authentication) ? "anonymous" : "not fully authenticated") + "); redirecting to authentication entry point",
						exception);

				sendStartAuthentication(
						request,
						response,
						chain,
						new InsufficientAuthenticationException(
							messages.getMessage(
								"ExceptionTranslationFilter.insufficientAuthentication",
								"Full authentication is required to access this resource")));
			}
			else {
				logger.debug(
						"Access is denied (user is not anonymous); delegating to AccessDeniedHandler",
						exception);

				accessDeniedHandler.handle(request, response,
						(AccessDeniedException) exception);
			}
		}
	}


	protected void sendStartAuthentication(HttpServletRequest request,
			HttpServletResponse response, FilterChain chain,
			AuthenticationException reason) throws ServletException, IOException {
		// SEC-112: Clear the SecurityContextHolder's Authentication, as the
		// existing Authentication is no longer considered valid
		SecurityContextHolder.getContext().setAuthentication(null);
		requestCache.saveRequest(request, response);
		logger.debug("Calling Authentication entry point.");
		authenticationEntryPoint.commence(request, response, reason);
	}
```

ExceptionTranslationFilter会在目标url调用commence方法之前，向HttpSession增加属性`AbstractAuthenticationProcessingFilter.SPRING_SECURITY_SAVED_REQUEST_KEY`。
实现类应该修改ServletResponse的headers，用于开始验证流程。
```java
public interface AuthenticationEntryPoint {

	void commence(HttpServletRequest request, HttpServletResponse response,
			AuthenticationException authException) throws IOException, ServletException;
}
```

{% asset_img AuthenticationEntryPoint.png %}

以基本的http验证为例：
```java
public class BasicAuthenticationEntryPoint implements AuthenticationEntryPoint,
		InitializingBean {

	public void commence(HttpServletRequest request, HttpServletResponse response,
			AuthenticationException authException) throws IOException {
		response.addHeader("WWW-Authenticate", "Basic realm=\"" + realmName + "\"");
		response.sendError(HttpStatus.UNAUTHORIZED.value(), HttpStatus.UNAUTHORIZED.getReasonPhrase());
	}

}
```

如果是cas协议，则发送重定向，跳转至登录页
```java
public class CasAuthenticationEntryPoint implements AuthenticationEntryPoint,
		InitializingBean {

	public final void commence(final HttpServletRequest servletRequest,
			final HttpServletResponse response,
			final AuthenticationException authenticationException) throws IOException {

		final String urlEncodedService = createServiceUrl(servletRequest, response);
		final String redirectUrl = createRedirectUrl(urlEncodedService);

		preCommence(servletRequest, response);

		response.sendRedirect(redirectUrl);
	}
}
```

实际上会搭配DelegatingAuthenticationEntryPoint使用。
RequestMatcher使用模式匹配，找到不同请求使用的AuthenticationEntryPoint。
这样方便支持多种验证模式。
```java
public class DelegatingAuthenticationEntryPoint implements AuthenticationEntryPoint,
		InitializingBean {

	public void commence(HttpServletRequest request, HttpServletResponse response,
			AuthenticationException authException) throws IOException, ServletException {

		for (RequestMatcher requestMatcher : entryPoints.keySet()) {
			if (logger.isDebugEnabled()) {
				logger.debug("Trying to match using " + requestMatcher);
			}
			if (requestMatcher.matches(request)) {
				AuthenticationEntryPoint entryPoint = entryPoints.get(requestMatcher);
				if (logger.isDebugEnabled()) {
					logger.debug("Match found! Executing " + entryPoint);
				}
				entryPoint.commence(request, response, authException);
				return;
			}
		}

		if (logger.isDebugEnabled()) {
			logger.debug("No match found. Using default entry point " + defaultEntryPoint);
		}

		// No EntryPoint matched, use defaultEntryPoint
		defaultEntryPoint.commence(request, response, authException);
	}
}
```


# Principal

Principal是java.security中定义的抽象，代表登录实体。
```java
public interface Principal {

    public String getName();
```

# Authentication

Authentication以token的形式，代表认证请求、或者已经认证的principal。
>Represents the token for an authentication request or for an authenticated principal once the request has been processed by the AuthenticationManager.authenticate(Authentication) method.

```java
public interface Authentication extends Principal, Serializable {
    /**
     * 由AuthenticationManager指定的授权
    */
	Collection<? extends GrantedAuthority> getAuthorities();

	/**
	 * The credentials that prove the principal is correct. This is usually a password,
	 * but could be anything relevant to the <code>AuthenticationManager</code>. Callers
	 * are expected to populate the credentials.
	 *
	 * @return the credentials that prove the identity of the <code>Principal</code>
	 */
	Object getCredentials();

	/**
	 * Stores additional details about the authentication request. These might be an IP
	 * address, certificate serial number etc.
	 *
	 * @return additional details about the authentication request, or <code>null</code>
	 * if not used
	 */
	Object getDetails();

	Object getPrincipal();

	boolean isAuthenticated();

	void setAuthenticated(boolean isAuthenticated) throws IllegalArgumentException;
}

```

Authentication有不同的实现类
{% asset_img AbstractAuthenticationToken.png %}

常见的有UsernamePasswordAuthenticationToken：
```java
public class UsernamePasswordAuthenticationToken extends AbstractAuthenticationToken {
	private final Object principal;
	private Object credentials;

	public UsernamePasswordAuthenticationToken(Object principal, Object credentials) {
		super(null);
		this.principal = principal;
		this.credentials = credentials;
        // 未验证，因此设置未false
		setAuthenticated(false);
	}    
```

紧密关联的是AuthenticationManager。

# AuthenticationManager

AuthenticationManager处理怎么验证Authentication对象。
```java
public interface AuthenticationManager {

    // 输入authentication对象，计算完整的authentication，包括授权（authorities）
	Authentication authenticate(Authentication authentication)
			throws AuthenticationException;
}
```

# AuthenticationProvider和ProviderManager

AuthenticationProvider用于处理Authentication请求。

ProviderManager是AuthenticationManager的一个实现，顺序调用AuthenticationProvider列表，直到其中一个返回非null。

```java
public class ProviderManager implements AuthenticationManager, MessageSourceAware,
		InitializingBean {

    // 省略其他成员
	private List<AuthenticationProvider> providers = Collections.emptyList();
	private AuthenticationManager parent;

	public Authentication authenticate(Authentication authentication)
			throws AuthenticationException {
		Class<? extends Authentication> toTest = authentication.getClass();
		AuthenticationException lastException = null;
		AuthenticationException parentException = null;
		Authentication result = null;
		Authentication parentResult = null;
		boolean debug = logger.isDebugEnabled();

		for (AuthenticationProvider provider : getProviders()) {
			if (!provider.supports(toTest)) {
				continue;
			}

			if (debug) {
				logger.debug("Authentication attempt using "
						+ provider.getClass().getName());
			}

			try {
				result = provider.authenticate(authentication);

				if (result != null) {
					copyDetails(authentication, result);
					break;
				}
			}
			catch (AccountStatusException | InternalAuthenticationServiceException e) {
				prepareException(e, authentication);
				// SEC-546: Avoid polling additional providers if auth failure is due to
				// invalid account status
				throw e;
			} catch (AuthenticationException e) {
				lastException = e;
			}
		}

		if (result == null && parent != null) {
			// Allow the parent to try.
			try {
				result = parentResult = parent.authenticate(authentication);
			}
			catch (ProviderNotFoundException e) {
				// ignore as we will throw below if no other exception occurred prior to
				// calling parent and the parent
				// may throw ProviderNotFound even though a provider in the child already
				// handled the request
			}
			catch (AuthenticationException e) {
				lastException = parentException = e;
			}
		}

		if (result != null) {
			if (eraseCredentialsAfterAuthentication
					&& (result instanceof CredentialsContainer)) {
				// Authentication is complete. Remove credentials and other secret data
				// from authentication
				((CredentialsContainer) result).eraseCredentials();
			}

			// If the parent AuthenticationManager was attempted and successful then it will publish an AuthenticationSuccessEvent
			// This check prevents a duplicate AuthenticationSuccessEvent if the parent AuthenticationManager already published it
			if (parentResult == null) {
				eventPublisher.publishAuthenticationSuccess(result);
			}
			return result;
		}

		// Parent was null, or didn't authenticate (or throw an exception).

		if (lastException == null) {
			lastException = new ProviderNotFoundException(messages.getMessage(
					"ProviderManager.providerNotFound",
					new Object[] { toTest.getName() },
					"No AuthenticationProvider found for {0}"));
		}

		// If the parent AuthenticationManager was attempted and failed then it will publish an AbstractAuthenticationFailureEvent
		// This check prevents a duplicate AbstractAuthenticationFailureEvent if the parent AuthenticationManager already published it
		if (parentException == null) {
			prepareException(lastException, authentication);
		}

		throw lastException;
	}

```
个人认为AccountStatusException这个抽象很好，在账号状态异常之后，避免后续provider继续检查。

AuthenticationManagerBuilder负责构建ProviderManager
```java
	protected ProviderManager performBuild() throws Exception {
		if (!isConfigured()) {
			logger.debug("No authenticationProviders and no parentAuthenticationManager defined. Returning null.");
			return null;
		}
		ProviderManager providerManager = new ProviderManager(authenticationProviders,
				parentAuthenticationManager);
		if (eraseCredentials != null) {
			providerManager.setEraseCredentialsAfterAuthentication(eraseCredentials);
		}
		if (eventPublisher != null) {
			providerManager.setAuthenticationEventPublisher(eventPublisher);
		}
		providerManager = postProcess(providerManager);
		return providerManager;
	}
```

# AbstractAuthenticationProcessingFilter

AbstractAuthenticationProcessingFilter是负责用户验证的filter。
Spring Security 提供了几个实现类：
- CasAuthenticationFilter
- OAuth2LoginAuthenticationFilter
- OpenIDAuthenticationFilter
- UsernamePasswordAuthenticationFilter

作为抽象类，定义了用户验证的流程。提供几个子类可以覆盖的行为（典型的template模式）：
- requiresAuthentication
- attemptAuthentication
- unsuccessfulAuthentication
- successfulAuthentication

```java
public abstract class AbstractAuthenticationProcessingFilter extends GenericFilterBean
		implements ApplicationEventPublisherAware, MessageSourceAware {

	private AuthenticationManager authenticationManager;

	public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
			throws IOException, ServletException {

		HttpServletRequest request = (HttpServletRequest) req;
		HttpServletResponse response = (HttpServletResponse) res;

		if (!requiresAuthentication(request, response)) {
			chain.doFilter(request, response);

			return;
		}

		if (logger.isDebugEnabled()) {
			logger.debug("Request is to process authentication");
		}

		Authentication authResult;

		try {
			authResult = attemptAuthentication(request, response);
			if (authResult == null) {
				// return immediately as subclass has indicated that it hasn't completed
				// authentication
				return;
			}
			sessionStrategy.onAuthentication(authResult, request, response);
		}
		catch (InternalAuthenticationServiceException failed) {
			logger.error(
					"An internal error occurred while trying to authenticate the user.",
					failed);
			unsuccessfulAuthentication(request, response, failed);

			return;
		}
		catch (AuthenticationException failed) {
			// Authentication failed
			unsuccessfulAuthentication(request, response, failed);

			return;
		}

		// Authentication success
		if (continueChainBeforeSuccessfulAuthentication) {
			chain.doFilter(request, response);
		}

		successfulAuthentication(request, response, chain, authResult);
	}
```

注意，不管验证成功还是失败，都要更新SecurityContext。
验证成功
```java
SecurityContextHolder.getContext().setAuthentication(authResult);
```
验证失败
```java
SecurityContextHolder.clearContext();
```


# AuthenticationConfigBuilder

AuthenticationConfigBuilder负责创建验证相关的filter。

```java
AuthenticationConfigBuilder(Element element, boolean forceAutoConfig,
		ParserContext pc, SessionCreationPolicy sessionPolicy,
		BeanReference requestCache, BeanReference authenticationManager,
		BeanReference sessionStrategy, BeanReference portMapper,
		BeanReference portResolver, BeanMetadataElement csrfLogoutHandler) {
    // more codes
	createAnonymousFilter();
	createRememberMeFilter(authenticationManager);
	createBasicFilter(authenticationManager);
	createBearerTokenAuthenticationFilter(authenticationManager);
	createFormLoginFilter(sessionStrategy, authenticationManager);
	createOAuth2LoginFilter(sessionStrategy, authenticationManager);
	createOAuth2ClientFilter(requestCache, authenticationManager);
	createOpenIDLoginFilter(sessionStrategy, authenticationManager);
	createX509Filter(authenticationManager);
	createJeeFilter(authenticationManager);
	createLogoutFilter();
	createLoginPageFilterIfNeeded();
	createUserDetailsServiceFactory();
	createExceptionTranslationFilter();
}
```
