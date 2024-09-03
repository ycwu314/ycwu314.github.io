---
title: "HTTP3 Part 8：QUIC 0-RTT"
date: 2024-09-03T10:21:38+08:00
tags: ["http3"]
categories: ["http3"]
description: QUIC 协议中的 0-RTT 能显著减少连接建立的延迟，但同时引入了重放攻击的风险。因此在0-RTT连接建立后，会进行1-RTT握手，协商新的密钥。
---

0-RTT 连接恢复背后的基本理念是，如果客户端和服务器之间之前已经建立了 TLS 连接，那么它们就可以使用缓存的会话信息建立新的连接，而无需重新协商连接参数。


# 0-RTT 的工作原理

初次连接：
- 当客户端第一次与服务器建立 QUIC 连接时，它会经历完整的握手过程，这通常涉及 1-RTT（一次往返时间）。在此过程中，客户端会从服务器获取必要的加密信息（如 TLS 证书）并完成加密会话的建立。
- 在这个过程中，服务器会向客户端提供一个 Session Ticket，用于后续的 0-RTT 连接。

后续连接（0-RTT）：
- 当客户端再次与同一服务器连接时，它可以使用之前收到的 Session Ticket，直接发起一个 0-RTT 连接请求。客户端使用预先协商好的密钥和协议版本加密并发送数据，无需等待服务器的响应。
- 服务器收到 0-RTT 请求后，可以直接处理并解密数据，从而实现更快的数据传输。


# 0-RTT 的安全问题

## 前向保密（Forward Secrecy） 

Forward Secrecy（前向安全性） 是一种密码学特性，确保即使长期使用的密钥（例如服务器的私钥）被泄露，之前的通信内容仍然无法被解密。这种安全特性是通过在每次会话中使用临时会话密钥来实现的，即便攻击者获得了长期密钥，也无法回溯性地解密以前的通信内容。

在 0-RTT 场景中，客户端使用的是之前会话中协商的预共享密钥（PSK），而不是每次重新生成的临时密钥。这和前向保密冲突。

## 重放攻击

由于 0-RTT 数据是客户端在没有与服务器完成完整握手的情况下发送的，这使得这些数据可能面临重放攻击的风险。攻击者可能会截获并重复发送 0-RTT 数据包，造成服务器的重复操作。

# 解决

## 缩短 Session Ticket 有效期

为了减小 PSK 泄露带来的风险，服务器通常会设置 Session Ticket 的短生命周期，确保 PSK 只在有限的时间窗口内有效。


## 更换长期密钥

客户端使用 0-RTT 请求与服务器建立连接后，长期密钥会在随后的握手过程中被更换。

0-RTT 阶段：
- 在 0-RTT 阶段，客户端使用之前从服务器获得的 Session Ticket 和相应的密钥进行加密通信。这些密钥是在之前的会话中通过完整的 TLS 1.3 握手生成的，并且允许客户端立即发送数据而无需等待新的握手完成。

1-RTT 阶段：
- 即使客户端在 0-RTT 阶段开始发送数据，QUIC 协议仍然要求双方完成一个完整的 TLS 1.3 握手，以建立一个新的加密上下文。这个完整的握手称为 1-RTT 握手。
- 在 1-RTT 握手中，客户端和服务器将协商新的加密密钥，并且所有后续的数据传输都将使用这些新的密钥进行加密。


# 总结

在 QUIC 协议中，0-RTT 阶段使用旧的密钥来加密初始数据，以实现低延迟连接。

然而，在 0-RTT 之后，协议要求客户端和服务器在 1-RTT 握手完成后使用新密钥进行后续的数据加密。这样做是为了确保通信的安全性，同时最大限度地减少延迟。

# 参考

- [The challenges of 0-RTT in IETF QUIC ](https://datatracker.ietf.org/meeting/115/materials/slides-115-tdd-sessa-challenges-of-0-rtt-in-ietf-quic-linked-from-deployment-talk-00)
- [Even faster connection establishment with QUIC 0-RTT resumption
](https://blog.cloudflare.com/even-faster-connection-establishment-with-quic-0-rtt-resumption/)
- [QUIC 0-RTT实现简析及一种分布式的0-RTT实现方案](https://cloud.tencent.com/developer/article/1594468)

