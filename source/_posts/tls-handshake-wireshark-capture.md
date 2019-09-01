---
title: 使用wireshark抓包tls 1.2握手
date: 2019-08-09 17:12:00
tags: [https, 技巧]
categories: [https]
keywords: [tls 抓包, encrypted handshake message, change cipher spec]
description: 使用wireshark对tls握手过程抓包。change cipher spec发生在双方。encrypted handshake message阶段表明握手结束，发送验证消息。
---

# 前言

上次聊了tls 1.2握手流程，内容比较多，缺乏具体的例子
- {% post_link tls-handshake-v-1-2 %}

这次以访问baidu首页为例，使用wireshark抓包，对其中的步骤进行观察。无图无真相，先上图，点击放大。
{% asset_img v1_baidu_handshake_capture.webp tls握手抓包 %}
<!-- more -->
# 查询dns

为了方便，关闭了浏览器，使用`curl`发起网络请求。
```bash
curl https://www.baidu.com
```
seq=9，发起了dns查询。
seq=10，dns服务器返回了baidu.com的ip地址。

# tcp三次握手

接下来3个数据包是熟悉的建立tcp连接三次握手。
seq=11，本机向baidu服务器发起tcp请求。发送的syn包。
seq=12，baidu服务器向本机回应syn ack包。
seq=13，本机发送ack，正式建立tcp连接。

# client hello

从第14个包开始，正式进入tls握手阶段。留意protocol=TLSv1.2。
{% asset_img v1_client_hello.webp "client hello" %}
核心的字段是TLS版本，client random，客户端支持的cipher suites。
还有其他扩展字段，比如之前提到的SNI，签名算法等。
{% asset_img v1_client_hello_extension.webp "client hello extension" %}

# server hello

第16个包开始是server hello阶段。
{% asset_img v1_server_hello.webp "server hello" %}
首先发送server random，以及协商使用的cipher suite
```
Cipher Suite: TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 (0xc02f)
```
`TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`的意义是:
- TLS：SSL/TLS协议
- ECDHE：key exchange 算法
- RSA：authentication 算法
- AES_128_GCM：encryptation算法
- SHA256： MAC 算法，用于创建消息摘要。后面的encrypted handshake message阶段用到。

第20个包发送了服务器证书。注意这里是2个证书，是baidu的证书，以及签发baidu的上级机构的证书
{% asset_img v1_server_hello_certificate.webp "server hello certificate" %}

打开baidu的证书。
{% asset_img v1_server_hello_certificate_detail.webp "server hello certificate" %}
可以看到几个关键信息：
1. 这个证书的制作，`sha256WithRSAEncryption`，sha256是验签方式，使用的非对称加密方式是RSA
2. `validity`记录证书的有效期
3. 这个证书的公钥public key



# server key exchange

第20个包有意思。
{% asset_img v1_server_key_exchange.webp "server key exchange" %}
上个文章提到，tls握手有2种模式：RSA握手、DH握手。这里再重复一下。
RSA握手模式，client自己生成premaster secret，并且使用证书的public key去加密，再发送给server。一旦服务器私钥泄露，未来所有的tls握手都不安全了。
DH握手模式，premaster secret由client、server根据DH parameter协商生成，安全性更高。

从抓包情况看，baidu使用了DH握手模式了。使用ECDH，返回了server dh param。

# server hello done

这个包很简单，没什么好说的。
{% asset_img v1_server_hello_done.webp "server hello done" %}

# client exchange阶段

第24个数据包内容很丰富。
{% asset_img v1_client_exchange.webp "client exchange" %}

## client key exchange

因为使用DH模式握手，client要回复它生产的client dh param
{% asset_img v1_client_key_exchange_dh_param.webp "client exchange"  %}

## change cipher spec（client）

这个包只有一个字节，但是干嘛呢？
{% asset_img v1_change_cipher_spec.webp "change cipher spec" %}

发现对这个数据包理解不到位，最后找到Cisco的一篇文章：[SSL Introduction with Sample Transaction and Packet Exchange](https://www.cisco.com/c/en/us/support/docs/security-vpn/secure-socket-layer-ssl/116181-technote-product-00.html)


>The message is sent by both the client and server in order to notify the receiving party that subsequent records are protected under the most recently negotiated Cipher Spec and keys.

1. client和server都会发送`change cipher spec`报文
{% asset_img v1_change_cipher_spec_overview.webp "change cipher spec" %}
2. 这个报文的意义是，通知对方，使用最近协商的cipher和key，并且后续的报文都是加密的。
{% asset_img v1_encrypt_handshake_message.webp "encrypt handshake message" %}

## encrypted handshake message

{% asset_img encrypt_handshake_message_detail.webp "encrypt handshake message" %}
tls握手成功之后，双方都会发送一条`encrypted handshake message`报文。这个报文的作用是校验握手是否成功，数据没有被中间人篡改。

>Both client and server send the Finished message but the first to do it is the client. If the server receives the message and could decrypt and understand it, it means the the server is reading the encrypted information in the right way. Now the only missing part is that client could decrypt the information sent by the server. To do that the server must send a Change Cipher Spec message too followed by the Finished message in the encrypted way. Exactly the same as client did. Again if the client could decrypt the Finished message it means that both parties are in frequency and they can talk to each other protecting all the data in transit.

1. client和server都会发送这个报文，但是首先由client发送
2. 发送的内容是什么呢，又是怎么验证？查到一个文章，讲的清楚 [TLS v1.2 handshake overview - apoorv munshi - Medium](https://medium.com/@ethicalevil/tls-handshake-protocol-overview-a39e8eee2cf5)

这个消息体的内容是一个hash，哈希方法使用的是server hello协商的`TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`中的SHA256。哈希的内容是
- master_secret
- hash of all the previous handshake messages (from ClientHello up to Finished message, not including this Finished Message)
- finished_label string (“client finished” for client message and “server finished” for server message) 
```
verify_data
         PRF(master_secret, finished_label, Hash(handshake_messages))
(quoted from section 7.4.9 of RFC 5246)
```
对方用同样方式计算，如果和哈希值一致，则表明安全建立加密通信。

# new session ticket

server生成会话id。
{% asset_img v1_new_session_ticket.webp "new session ticket" %}

# change cipher spec（server）

类似上面client的change cipher spec，不重复了。

# application data

从这个阶段开始，client和server使用session key加密、解密数据通信。
{% asset_img v1_application_data.webp "application data" %}

# 其他：[TCP Spurious Retransmissions]

{% asset_img v1_tcp_spurious_retransimission.webp "tcp spurious retransimission" %}
`spurious`的意思是虚假的。baidu服务器认为可能发生超时或者丢包，提前发起重传。具体以后再研究。



