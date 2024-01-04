---
title: "Zmodem 协议概述"
date: 2024-01-04T10:34:09+08:00
tags: ["linux"]
categories: []
description: 古老但也挺方便的zmodem协议。
---

>ZMODEM（ZModem）是一种用于在串行通信中进行高效文件传输的协议。它是XMODEM和YMODEM的进化版本，旨在提供更快、更可靠的文件传输，并支持一些先进的功能。ZMODEM协议主要用于通过串行线路（通常是RS-232串行端口）进行文件传输。

zmodem协议比较古老了，但是客户端支持的话（xshell、tabby）可以方便弹起上传、下载窗口，传输少量小体积的文件挺方便的。

可惜sshwifty暂时不支持zmodem协议。

目前看到比较完整的参考资料：

https://wiki.synchro.net/ref:zmodem



# 安装

zmodem需要服务器端、客户端都安装。

```shell
apt install -y lrzsz 
```

# zmodem frame

ZMODEM Frames:
- Hexadecimal (HEX) frames, containing only US-ASCII characters

```
<frame header> [CR] LF [XON]
```

- Binary (BIN16 or BIN32) frames, containing almost all possible octet values

```
<frame header> [[<* data subpacket> [...]] <ZCRCW | ZCRCE data subpacket>]
```


在ZMODEM协议中，Hexadecimal (HEX) frames 和 Binary (BIN16 or BIN32) frames 有着不同的用途：

1. **Hexadecimal (HEX) Frames:**
   - **用途：** 主要用于可读性较高的日志、调试信息或人类可解释的文本表示。这类帧通常被用于调试和分析 ZMODEM 传输时的问题，因为它们以十六进制形式展示，易于人类理解。
   - **示例：** HEX 帧可能会在调试日志中看到，例如 `2A 2A 18 42 06 6E 6E 78 78 78 78 0D 0A 1A` 这样的序列，表示 ZDATA 帧。

2. **Binary (BIN16 or BIN32) Frames:**
   - **用途：** 包含了实际的二进制数据，用于在通信链路上传输文件。这类帧包含了文件的原始二进制内容，而不是经过任何特殊字符编码的表示。它们是 ZMODEM 传输的实际有效载荷。
   - **示例：** BINARY 帧不太适合人类直接观察，因为它们可能包含各种二进制数据，例如文件内容的字节。

# Frame Header

```
<frame encoding> <frame type> <frame info> <checksum>
```

frame encoding: 1 byte

frame type: 1 byte

frame info: Up to 15 bytes (but typically 4) 

checksum: either a 16-bit or 32-bit CRC (determined by the frame encoding)

## Frame Encoding  

| Style  | AKA    | Value         | Frame Contents                           | Checksum   |
|--------|--------|---------------|------------------------------------------|------------|
| HEX    | ZHEX   | ASCII 'B'     | Hexadecimal/US-ASCII characters only     | 16-bit CRC  |
| BIN16  | ZBIN   | ASCII 'A'     | Binary                                   | 16-bit CRC  |
| BIN32  | ZBIN32 | ASCII 'C'     | Binary                                   | 32-bit CRC  |

## Frame Type 

| Type     | Value | TX1) | RX2) | Info     | Data Subpkt     | Notes                                |
|----------|-------|------|------|----------|-----------------|--------------------------------------|
| ZRQINIT  | 0x00  | Y    | -    | caps     | -               | Request ZRINIT from the receiver    |
| ZRINIT   | 0x01  | -    | Y    | caps     | -               | Receiver Initialized                |
| ZSINIT   | 0x02  | Y    | -    | flags    | Attn sequence   | Sender Initialized                   |
| ZACK     | 0x03  | Y    | Y    | offset   | -               | Positive Acknowledgment              |
| ZFILE    | 0x04  | Y    | -    | options  | File metadata  | File information (name/len/date)    |
| ZSKIP    | 0x05  | -    | Y    | -        | -               | Skip (don't send) this file          |
| ZNAK     | 0x06  | Y    | Y    | -        | -               | Negative Acknowledgment              |
| ZABORT   | 0x07  | -    | Y    | -        | -               | Terminate batch file transfer        |
| ZFIN     | 0x08  | Y    | -    | -        | -               | Terminate transfer session           |
| ZRPOS    | 0x09  | -    | Y    | offset   | -               | Reposition the send offset           |
| ZDATA    | 0x0A  | Y    | -    | offset   | File contents   | One or more data subpackets follow   |
| ZEOF     | 0x0B  | Y    | -    | offset   | -               | End of file reached                  |
| ZFERROR  | 0x0C  | -    | Y    | -        | -               | File I/O error                       |
| ZCRC     | 0x0D  | Y    | Y    | CRC-32   | -               | File CRC request/response            |
| ZFREECNT | 0x11  | Y    | -    | f-space  | -               | Request free disk space              |


## Data Subpacket

```
<data> ZDLE <subpacket type> <crc>
```

数据包长度最大1KB。ZedZap等实现支持最大8KB。

`ZDLE` is the ZMODEM Data-link-escape character (^X, ASCII 24).

### Data Subpacket Types

| Type  | ZACK/ZRPOS expected | End-of-Frame | Meaning | Notes |
|-------|----------------------|--------------|---------|-------|
| ZCRCW | Yes (synchronous)    | Yes          | Wait or Write | "ZCRCW data subpackets expect a response before the next frame is sent ... to allow the receiver to write its buffer before sending more data" |
| ZCRCE | Only errors          | Yes          | End     | "If the end of file is encountered within a frame, the frame is closed with a ZCRCE data subpacket which does not elicit a response except in case of error" |
| ZCRCQ | Yes (asynchronous)   | No           | Query   | "ZCRCQ subpackets are not used if the receiver does not indicate full duplex ability with the [ZRINIT] CANFDX bit" |
| ZCRCG | Only errors          | No           | Go      | "ZCRCG subpackets do not elicit a response unless an error is detected" |

# LINK ESCAPE ENCODING

Link Escape Encoding（链路转义编码）是一种通信协议中的技术，用于在数据传输过程中转义特殊字符，以确保数据的准确性和透明性。在ZMODEM协议中，链路转义编码是通过特殊的转义字符ZDLE（ZMODEM Data Link Escape）来实现的。

具体来说，链路转义编码有以下几个目的和特点：

1. **扩展字符集：** 链路转义编码允许在原始的8位字符集（256个代码）的基础上引入转义序列，以表示特殊的命令或控制信息。

2. **透明传输：** 通过使用ZDLE作为转义字符，链路转义编码允许传输二进制数据而不受到数据中特殊字符的影响。这样可以确保数据的透明性，即发送方发送的数据可以在接收方被准确地重建。

3. **可变长度数据子包：** 链路转义编码允许可变长度的数据子包，而无需在每个子包中使用独立的字节计数字段。这有助于减少传输的开销。

4. **错误检测和恢复：** 通过引入ZDLE作为控制字符，链路转义编码使得在传输过程中检测到帧的开始变得更加容易，从而有助于进行快速的错误恢复。


接收程序会解码任何ZDLE后跟带有第6位设置和第5位复位（大写字母，任一奇偶校验）的字节序列，将其转换为等效的控制字符，方法是反转第6位。这允许发送方转义无法通过通信介质发送的任何控制字符。此外，接收方还会识别0x7f和0xff的转义，以防这些字符需要转义。

zmodem软件会转义ZDLE（0x18）、0x10、0x90、0x11、0x91、0x13和0x93。

如果在0x40或0xc0（@）之前，0x0d和0x8d也会被转义，以保护Telenet命令转义CR-@-CR。接收器会在数据流中忽略0x11、0x91、0x13和0x93字符。

总体而言，链路转义编码是一种在通信协议中用于确保数据传输的正确性和透明性的技术。在ZMODEM中，ZDLE起到了关键的作用，表示后续字符是一种控制序列或者需要进行转义处理。

## 额外开销

链路转义编码确实增加了一些开销。最坏的情况是，一个完全由转义字符组成的文件会产生50%的开销。

## 会话终止

连续出现的五个CAN字符会中断zmodem会话。

由于在正常的终端操作、交互式应用程序和通信程序中不使用CAN，因此这些应用可以监视数据流以检测ZDLE。以下字符可以扫描以检测ZRQINIT标头，即自动下载命令或文件的邀请。

**连续接收到五个CAN字符将中断zmodem会话。发送了八个CAN字符（为了安全起见）。**


# 协议流程

大概流程

```
  +-----------------------+       +-----------------------+
  |      Sender Side      |       |      Receiver Side    |
  +-----------------------+       +-----------------------+
              |                             |
              |         ZRQINIT Frame       |
              | --------------------------> |
              |                             |
              |         ZRINIT Frame        |
              | <-------------------------- |
              |                             |
              |                             |
              |                             |
              |        ZFILE Frame          |
              | --------------------------> |
              |                             |
              |                             |
              |                             |
              |         ZDATA Frames        |
              | --------------------------> |
              |                             |
              |                             |
              |                             |
              |         ZCRCW Frame         |
              | --------------------------> |
              |                             |
              |                             |
              |                             |
              |         ZACK Frame          |
              | <-------------------------- |
              |                             |
              |                             |
              |                             |
              |         ZFIN Frame          |
              | --------------------------> |
              |                             |
              |                             |
              |                             |
              |        ZFINACK Frame        |
              | <-------------------------- |
              |                             |
              +-----------------------------+

```

更多细节参考 https://wiki.synchro.net/ref:zmodem

# zmodem和scp的对比

gpt整理的。


ZMODEM和SCP是两种不同的文件传输协议，它们分别用于在计算机系统之间安全地传输文件。以下是它们之间的一些主要区别：

1. **安全性：**
   - **ZMODEM：** ZMODEM不提供加密功能，因此文件传输过程中的数据是明文的。在不安全的网络环境中，可能需要使用额外的安全通道（例如SSH）来保护数据。
   - **SCP：** SCP（Secure Copy Protocol）建立在SSH（Secure Shell）之上，通过使用SSH提供的加密机制来保护传输的文件的机密性。因此，SCP具有更高的安全性，适用于在不受信任的网络中进行文件传输。

2. **协议和用途：**
   - **ZMODEM：** ZMODEM是一个用于串行通信协议的文件传输协议，通常用于通过串行端口（例如RS-232）进行文件传输。它通过透明地传输二进制数据来实现高效的文件传输。
   - **SCP：** SCP是一个用于通过SSH进行加密的网络文件传输协议。它适用于在网络上安全地传输文件，而不需要额外的加密通道。

3. **传输效率：**
   - **ZMODEM：** ZMODEM通过使用一系列优化技术，如数据透明性、数据窗口和数据压缩，以提高文件传输的效率。它专注于串行通信的高效传输。
   - **SCP：** SCP通过SSH进行文件传输，具有较好的安全性，但可能在传输效率上略逊于专门针对传输效率进行优化的协议，如ZMODEM。

4. **使用场景：**
   - **ZMODEM：** 通常用于传统的串行通信环境，例如通过串行电缆连接的两台计算机之间的文件传输。
   - **SCP：** 更适用于通过网络连接的计算机之间进行安全文件传输，特别是在需要对传输的数据进行加密的情况下。

