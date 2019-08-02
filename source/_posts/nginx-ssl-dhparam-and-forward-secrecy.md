---
title: nginx配置dhparam，以及聊聊forward secrecy
date: 2019-07-24 00:20:55
tags: [nginx, https, devops]
categories: [nginx]
keywords: [nginx dhparam, nginx forward secrecy, 前向保密, premaster secret]
description: DHE或者ECDHE算法能够包换premaster secret（前向保密）的交换，从而实现forward secrecy，nginx使用openssl默认生成的dhparam是1024bit，强度低；因此要手动生成高强度的dhparam。
---

# Forward Secrecy，前向保密

>前向保密（英语：Forward Secrecy，FS），有时也被称为完全前向保密（英语：Perfect Forward Secrecy，PFS）。长期使用的主密钥泄漏不会导致过去的会话密钥泄漏。

要理解Forward Secrecy，要先理解TLS连接的建立过程。

# 基于RSA的SSL握手

![](https://www.cloudflare.com/resources/images/slt3lc6tev37/HMtyedlloYodaGnzxFcON/176dea4dbf1c8b4f3d58e6afd43ee9ea/ssl-handshake-rsa.jpg)

1. client发送client hello信息，包括：协议版本，支持的加密套件，以及随机数据“client random”。（明文）
2. server响应，包括：SSL证书（RSA public key），优先使用的加密套件，以及随机数据“server random”。（明文）
3. client创建新的随机数据，“premaster secret”，然后用step2返回的SSL证书加密premaster secret，发送给server。（密文）
4. server使用RSA private key解密step3的内容，得到明文的premaster secret。
5. 现在client，server都得到了client random，server random和premaster。把这3者组合得到session key，后续通讯基于此session key。

这个方案的安全性基于只有server知道private key。一旦private key泄露，那么所有使用这个SSL证书的密文premaster secret都能被解密！
这个方案的问题在于，private key既用于SSL证书身份识别（authentication），又用于premaster secret的解密。
因此解决思路是，改变交换premaster secret的方式。

# 基于DH的SSL握手

Ephemeral Diffie-Hellman (DHE)算法（ephemeral是临时的意思，表明同一个key不会使用两次），是其中一种解决premaster secret交换安全性的算法。
RSA握手方式，premaster由client生成，并且加密。但是DHE算法，client和server使用协商的DH param，分别计算premaster secret。

![](https://www.cloudflare.com/resources/images/slt3lc6tev37/1mzPVvjnKpVD0LUSsUlq2r/23c6dee053aaab22b122b53783dc098f/ssl-handshake-diffie-hellman.jpg)

1. client发送client hello信息，包括：协议版本，支持的加密套件，以及随机数据“client random”。（明文）
2. server响应，包括：SSL证书（RSA public key），优先使用的加密套件，随机数据“server random”，server DH param。**并且使用privae key对client random，server random，DH参数加密**。（密文）
3. client用public key解密step2，验证（authentication）了服务器身份，并且得到server DH param。client回复client DH param。
4. 现在client和server都有client DH param，server DH param，分别计算，得到premaster secret。
5. client和server都有client random，server random，premaster，组合得到session key。

注意到private key只在step2使用。即使private key泄露，也只得到一个临时的DH param。
因为premaster secret是每个session生成、不在网络上传输、**并且不经过长期密钥加密**，除非攻击每个session，否则会话是安全的。从而实现Forward Secrecy。

DH算法具体的数学原理此处不展开了。

# 支持FS的加密算法

- 基于DHE，包括DHE-RSA和DHE-DSA
- 基于椭圆曲线迪菲-赫尔曼密钥交换（ECDHE）包括，ECDHE-RSA与ECDHE-ECDSA

DHE算法的缺点是计算开销大。优先选择ECDHE，性能更好。


# nginx配置

nginx开启FP的条件：
- cipher suite是ECDHE或者DHE(ps. TLSv1.3只支持PFS的ciphers)
- 配置dhparam

这里有个坑，nginx使用openssl生产DH参数，默认是1024bit，强度太低，至少是2048以上才行。

1. 生成dhparam
```
openssl dhparam -out dhparam.pem 2048
```

2. 更新配置server
```
ssl_dhparam cert/dhparam.pem;
ssl_ecdh_curve X25519:prime256v1:secp384r1;
```
# 参考资料

- [Perfect Forward Secrecy - Why You Should Be Using It](https://www.keycdn.com/blog/perfect-forward-secrecy)
- [How Does Keyless SSL Work? | Forward Secrecy](https://www.cloudflare.com/learning/ssl/keyless-ssl/)

