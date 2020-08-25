---
title: zuul向后端服务传递Principal
date: 2020-08-25 11:12:25
tags: [zuul, java]
categories: [java]
keywords: [zuul principal]
description: 
---

在网关层对接cas client之后，后端服务不能正常获取当前登录用户信息。
<!-- more -->

# getUserPrincipal和getRemoteUser

`HttpServletRequest`定义了获取登录用户的方法。
```java

/**
 * Returns a <code>java.security.Principal</code> object containing the name
 * of the current authenticated user. If the user has not been
 * authenticated, the method returns <code>null</code>.
 *
 * @return a <code>java.security.Principal</code> containing the name of the
 *         user making this request; <code>null</code> if the user has not
 *         been authenticated
 */
public java.security.Principal getUserPrincipal();


/**
 * Returns the login of the user making this request, if the user has been
 * authenticated, or <code>null</code> if the user has not been
 * authenticated. Whether the user name is sent with each subsequent request
 * depends on the browser and type of authentication. Same as the value of
 * the CGI variable REMOTE_USER.
 *
 * @return a <code>String</code> specifying the login of the user making
 *         this request, or <code>null</code> if the user login is not known
 */
public String getRemoteUser();
```

不同的servlet容器实现会有差异。
tomcat对应实现类在`org.apache.catalina.connector.Request`：
```java
public Principal getUserPrincipal() {
    if (userPrincipal instanceof TomcatPrincipal) {
        GSSCredential gssCredential =
                ((TomcatPrincipal) userPrincipal).getGssCredential();
        if (gssCredential != null) {
            int left = -1;
            try {
                left = gssCredential.getRemainingLifetime();
            } catch (GSSException e) {
                log.warn(sm.getString("coyoteRequest.gssLifetimeFail",
                        userPrincipal.getName()), e);
            }
            if (left == 0) {
                // GSS credential has expired. Need to re-authenticate.
                try {
                    logout();
                } catch (ServletException e) {
                    // Should never happen (no code called by logout()
                    // throws a ServletException
                }
                return null;
            }
        }
        return ((TomcatPrincipal) userPrincipal).getUserPrincipal();
    }
    return userPrincipal;
}

public String getRemoteUser() {
    if (userPrincipal == null) {
        return null;
    }
    return userPrincipal.getName();
}


public void setUserPrincipal(final Principal principal) {
    if (Globals.IS_SECURITY_ENABLED && principal != null) {
        if (subject == null) {
            final HttpSession session = getSession(false);
            if (session == null) {
                // Cache the subject in the request
                subject = newSubject(principal);
            } else {
                // Cache the subject in the request and the session
                subject = (Subject) session.getAttribute(Globals.SUBJECT_ATTR);
                if (subject == null) {
                    subject = newSubject(principal);
                    session.setAttribute(Globals.SUBJECT_ATTR, subject);
                } else {
                    subject.getPrincipals().add(principal);
                }
            }
        } else {
            subject.getPrincipals().add(principal);
        }
    }
    userPrincipal = principal;
}
```

可见，remoteUser是从`userPrincipal#getName()`获取。

思路：
1. zuul filter传递principal到某个header
2. 后端服务解析该header，得到登录的用户名

后端服务如果要更新userPrincipal，则需要适配不同servlet容器，侵入性太强。
更好的做法是，使用filter + 自定义request wrapper + 重载`getRemoteUser()`的方式。

# zuul filter

```java
/**
 * 向后端服务传递登录用户
 */
@Component
public class TransmitPrincipalFilter extends ZuulFilter {

    public static final String PRINCIPAL_HEADER = "X-GATEWAY-PRINCIPAL-NAME";

    @Override
    public String filterType() {
        return "pre";
    }

    /**
     * must after login filter
     *
     * @return
     */
    @Override
    public int filterOrder() {
        return 2000;
    }

    @Override
    public boolean shouldFilter() {
        return RequestContext.getCurrentContext().getRequest().getUserPrincipal() != null;
    }

    @Override
    public Object run() throws ZuulException {
        RequestContext ctx = RequestContext.getCurrentContext();
        Principal principal = ctx.getRequest().getUserPrincipal();

        if (principal != null) {
            ctx.addZuulRequestHeader(PRINCIPAL_HEADER, principal.getName());
        }

        return null;
    }
}

```

后端filter和request wrapper就不贴了。

