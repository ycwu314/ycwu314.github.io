---
title: cas logout 分析
date: 2020-03-03 17:54:58
tags: [cas, sso]
categories: [cas]
keywords: [cas logout]
description: cas logout分为单个应用登出和sso登出。sso登出的实现又分为back channel和front channel两种。
---

基于cas server 4.x 代码。

# CAS logout 类型

cas有2种类型的登出：
- 应用登出。结束单个应用的session。不会影响其他应用的session状态。
- CAS登出。结束cas sso session。缩写为SLO（Single Logout）。影响所有应用。

<!-- more -->

应用session和cas sso session的关系如下图（来源自cas 官网）：
{% asset_img sso-session-vs-application-session.png sso-session-vs-application-session %}


# SLO 请求类型

SLO请求分为2种，BACK_CHANNEL 和 FRONT_CHANNEL 。定义在`LogoutType`:
```java
package org.jasig.cas.services;

public enum LogoutType {
    /**
    * For no SLO.
    */
    NONE,
    /**
     * For back channel SLO.
     */
    BACK_CHANNEL,
    /**
     * For front channel SLO.
     */
    FRONT_CHANNEL
}
```
CAS SLO 默认是BACK_CHANNEL模式。

所谓的back、 front，是指在cas server端/web端向各个应用发送logout通知。

## SLO back channel

CAS server向各个接入的service发送post消息。这个操作是best-effort but no promise，但在通常情况下表现还好。

## SLO front channel

在CAS 4.x，SLO front channel是实验特性，借鉴了SAML SLO。
CAS server返回`RelayState`和重定向，再由客户端向各个service发起logout通知。

这个proposal描述了front channel的流程：[Proposal: Front-Channel Single Sign-Out](https://apereo.atlassian.net/wiki/spaces/CAS/pages/102927063/Proposal+Front-Channel+Single+Sign-Out)，引用里面的时序图描述了SLO front channel的流程，一目了然：

{% asset_img FrontChannelSingleSignOutSequence.png slo-front-channel-sequence %}



## back channel vs front channel

back channel模式，由cas server承载通信压力，通知各个service logout。
与之相反，front channel模式，需要前端向各个service发送logout通知。
站在前端角度看，back channel发送更少的网络请求，体验更好。
但是back channel可能不能正确处理接入负载均衡的service logout。如果load balance跟client绑定，那么由cas server代替client发送向service发送logout请求，可能不会落到对应service所在机器上。如果该service的session不是存储在共享存储（比如记录在redis、mysql等），而只是保存在单实例内存，那么这个logout请求不能正确清除对应账号的session状态。

为了处理这个场景，cas引入了front channel模式，由client向各个service发送logout请求。

## service 配置

```json
{
  "@class" : "org.jasig.cas.services.RegexRegisteredService",
  "serviceId" : "testId",
  "name" : "testId",
  "id" : 1,
  // SLO类型， 默认 BACK_CHANNEL
  "logoutType" : "BACK_CHANNEL",
  // service 回调接口
  "logoutUrl" : "https://web.application.net/logout",
}
```

# CAS logout 流程分析

cas 4.x使用spring webflow配置流程。对应logout流程配置在`logout-webflow.xml`。
入口是`terminateSession`。
```xml
  <action-state id="terminateSession">
    <evaluate expression="terminateSessionAction.terminate(flowRequestContext)" />
    <transition to="doLogout" />
  </action-state>
```

终结SSO session要做的事情：
- 清理TGT
- 清理sso session管理的cookies

## slo back channel

实现入口在`TerminateSessionAction`:
```java
public class TerminateSessionAction {
    /**
     * Terminates the CAS SSO session by destroying the TGT (if any) and removing cookies related to the SSO session.
     *
     * @param context Request context.
     *
     * @return "success"
     */
    public Event terminate(final RequestContext context) {
        // in login's webflow : we can get the value from context as it has already been stored
        String tgtId = WebUtils.getTicketGrantingTicketId(context);
        // for logout, we need to get the cookie's value
        if (tgtId == null) {
            final HttpServletRequest request = WebUtils.getHttpServletRequest(context);
            tgtId = this.ticketGrantingTicketCookieGenerator.retrieveCookieValue(request);
        }
        // 清理TGT
        if (tgtId != null) {
            WebUtils.putLogoutRequests(context, this.centralAuthenticationService.destroyTicketGrantingTicket(tgtId));
        }
        final HttpServletResponse response = WebUtils.getHttpServletResponse(context);
        // 清理对应cookies
        this.ticketGrantingTicketCookieGenerator.removeCookie(response);
        this.warnCookieGenerator.removeCookie(response);
        return this.eventFactorySupport.success(this);
    }
}
```

CentralAuthenticationService负责清理TGT。默认实现是`CentralAuthenticationServiceImpl`:
```java
// 处理slo back channel
public List<LogoutRequest> destroyTicketGrantingTicket(@NotNull final String ticketGrantingTicketId) {
    try {
        logger.debug("Removing ticket [{}] from registry...", ticketGrantingTicketId);
        final TicketGrantingTicket ticket = getTicket(ticketGrantingTicketId, TicketGrantingTicket.class);
        logger.debug("Ticket found. Processing logout requests and then deleting the ticket...");
        // 由 LogoutManager 处理 SLO
        final List<LogoutRequest> logoutRequests = logoutManager.performLogout(ticket);
        // 清理TGT
        this.ticketRegistry.deleteTicket(ticketGrantingTicketId);
        return logoutRequests;
    } catch (final InvalidTicketException e) {
        logger.debug("TicketGrantingTicket [{}] cannot be found in the ticket registry.", ticketGrantingTicketId);
    }
    return Collections.emptyList();
}
```

LogoutManager根据service配置，处理back channel logout：
```java
/**
 * Perform a back channel logout for a given ticket granting ticket and returns all the logout requests.
 *
 * @param ticket a given ticket granting ticket.
 * @return all logout requests.
 */
@Override
public List<LogoutRequest> performLogout(final TicketGrantingTicket ticket) {
    final Map<String, Service> services = ticket.getServices();
    final List<LogoutRequest> logoutRequests = new ArrayList<>();
    // if SLO is not disabled
    if (!this.singleLogoutCallbacksDisabled) {
        // through all services
        for (final Map.Entry<String, Service> entry : services.entrySet()) {
            // it's a SingleLogoutService, else ignore
            final Service service = entry.getValue();
            if (service instanceof SingleLogoutService) {
                final LogoutRequest logoutRequest = handleLogoutForSloService((SingleLogoutService) service, entry.getKey());
                if (logoutRequest != null) {
                    LOGGER.debug("Captured logout request [{}]", logoutRequest);
                    logoutRequests.add(logoutRequest);
                }
            }
        }
    }
    return logoutRequests;
}

// 获取service配置，构建DefaultLogoutRequest
private LogoutRequest handleLogoutForSloService(final SingleLogoutService singleLogoutService, final String ticketId) {
    if (!singleLogoutService.isLoggedOutAlready()) {
        final RegisteredService registeredService = servicesManager.findServiceBy(singleLogoutService);
        if (serviceSupportsSingleLogout(registeredService)) {
            final URL logoutUrl = determineLogoutUrl(registeredService, singleLogoutService);
            final DefaultLogoutRequest logoutRequest = new DefaultLogoutRequest(ticketId, singleLogoutService, logoutUrl);
            final LogoutType type = registeredService.getLogoutType() == null
                    ? LogoutType.BACK_CHANNEL : registeredService.getLogoutType();
            switch (type) {
                case BACK_CHANNEL:
                    if (performBackChannelLogout(logoutRequest)) {
                        logoutRequest.setStatus(LogoutRequestStatus.SUCCESS);
                    } else {
                        logoutRequest.setStatus(LogoutRequestStatus.FAILURE);
                        LOGGER.warn("Logout message not sent to [{}]; Continuing processing...", singleLogoutService.getId());
                    }
                    break;
                default:
                    logoutRequest.setStatus(LogoutRequestStatus.NOT_ATTEMPTED);
                    break;
            }
            return logoutRequest;
        }
    }
    return null;
}    

// 向service发送logout通知
private boolean performBackChannelLogout(final LogoutRequest request) {
    try {
        final String logoutRequest = this.logoutMessageBuilder.create(request);
        final SingleLogoutService logoutService = request.getService();
        logoutService.setLoggedOutAlready(true);

        LOGGER.debug("Sending logout request for: [{}]", logoutService.getId());
        final LogoutHttpMessage msg = new LogoutHttpMessage(request.getLogoutUrl(), logoutRequest);
        LOGGER.debug("Prepared logout message to send is [{}]", msg);
        return this.httpClient.sendMessageToEndPoint(msg);
    } catch (final Exception e) {
        LOGGER.error(e.getMessage(), e);
    }
    return false;
}
```


## slo front channel 

还是`logout-webflow.xml`
```xml
<action-state id="frontLogout">
  <evaluate expression="frontChannelLogoutAction" />
  <transition on="finish" to="finishLogout" />
  <transition on="redirectApp" to="redirectToFrontApp" />
</action-state>
```

FrontChannelLogoutAction是入口：
```java
public final class FrontChannelLogoutAction extends AbstractLogoutAction {

    @Override
    protected Event doInternalExecute(final HttpServletRequest request, final HttpServletResponse response,
            final RequestContext context) throws Exception {

        final List<LogoutRequest> logoutRequests = WebUtils.getLogoutRequests(context);
        final Integer startIndex = getLogoutIndex(context);
        if (logoutRequests != null) {
            for (int i = startIndex; i < logoutRequests.size(); i++) {
                final LogoutRequest logoutRequest = logoutRequests.get(i);
                if (logoutRequest.getStatus() == LogoutRequestStatus.NOT_ATTEMPTED) {
                    // assume it has been successful
                    logoutRequest.setStatus(LogoutRequestStatus.SUCCESS);

                    // save updated index
                    putLogoutIndex(context, i + 1);

                    final String logoutUrl = logoutRequest.getLogoutUrl().toExternalForm();
                    LOGGER.debug("Using logout url [{}] for front-channel logout requests", logoutUrl);

                    final String logoutMessage = logoutManager.createFrontChannelLogoutMessage(logoutRequest);
                    LOGGER.debug("Front-channel logout message to send under [{}] is [{}]",
                            this.logoutRequestParameter, logoutMessage);

                    // redirect to application with SAML logout message
                    final UriComponentsBuilder builder = UriComponentsBuilder.fromHttpUrl(logoutUrl);
                    builder.queryParam(this.logoutRequestParameter, URLEncoder.encode(logoutMessage, "UTF-8"));

                    return result(REDIRECT_APP_EVENT, DEFAULT_FLOW_ATTRIBUTE_LOGOUT_URL, builder.build().toUriString());
                }
            }
        }

        // no new service with front-channel logout -> finish logout
        return new Event(this, FINISH_EVENT);
    }

}
```

实现要点：
- 获取所有的logout request
- 分别向各个service创建SAML logout message（其实是处理一个就return了）。注意使用了redirect并且return。因此发送单个logout请求后，更新了spring webflow的state，再由前端触发front channel action逻辑，再次进入。

saml格式的logout message，参照上面的front channel时序图。

## 小结

- back channel入口在TerminateSessionAction
- front channel入口在FrontChannelLogoutAction
- LogoutManager提供了back channel和front channel的实现

# case: CAS client无法全部logout

上面已经分析过，service的负载均衡方式和session存储的实现方式，可能导致cas server向service发送的logout请求不能被正确处理。
解决方式：
- 由client向各个service发送logout请求，即SLO front channel。
- service的session，使用统一存储，比如redis、mysql，而非应用in-memory方式。

# 参考

- [Logout and Single Logout (SLO)](https://apereo.github.io/cas/4.2.x/installation/Logout-Single-Signout.html)




