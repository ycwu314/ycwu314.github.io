---
title: reactor模式
date: 2019-08-13 21:42:24
tags: [高并发, netty, IO]
categories: [设计模式]
keywords: [thread per connection, IO多路复用, reactor模式, 同步事件分离器, io multiplexing]
description: reactor模式基于IO多路复用模型。acceptor线程负责和client建立连接。由同步事件分离器检查就绪IO通道，并且交给NIO线程池负责处理IO读写请求。
---

在这篇文章简单介绍了linux IO模型。
- {% post_link io-model %}

其中一种模型是**IO多路复用**，并且产生了**Reactor模式**。这次就继续聊聊Reactor模式。
<!-- more -->

# 阻塞IO模型的性能瓶颈

首先回顾下blocking io的处理流程
{% asset_img blocking_io_model.png "blocking io model" %}

如果IO操作不能及时返回，那么整个线程就会被阻塞。
```
while(true){ 
    socket = accept(); 
    handle(socket) 
} 
```
在阻塞模式，要提升高并发性能，只能增加线程数，使用`thread per connection`的模式。
{% asset_img Thread-per-connection-thread-behavior.png "thread per connection" %}
```
while(true){ 
    socket = accept(); 
    new handler_thread(socket); 
} 
```
可是线程的创建和销毁带来性能损耗。于是使用线程池来管理线程的生命周期，尽量重用线程。
但是线程切换上下文的开销是无法避免的。再高的并发就扛不住了。

# reactor模式

正因为阻塞IO的缺点，演化出非阻塞IO、IO多路复用等模型。reactor模式使用了IO多路复用模型。
回顾IO多路复用流程
{% asset_img io_multiplexing.png "io multiplexing" %}

IO多路复用使用select函数或者epoll函数，这2个函数也是阻塞调用，但是一次能够检查多个IO操作。
那么，可以只使用一个主线程来检查IO状态，如果发现就绪，就交给另一个线程去处理底层的IO操作；主线程继续检查其他IO操作状态。
这就是reactor模式的核心思想。

{% asset_img reactor_pattern.png "reactor pattern" %}

典型的reactor模式包含以下组件：
- dispatcher。派分器。注册、移除事件处理器。
- synchronous event demultiplexer。同步事件分离器。使用select之类的方法，阻塞等待资源就绪。一旦资源就绪，通知事件处理器处理。
- handle。资源句柄。例如socket。
- event handler。通用的事件处理器。
- concret event hanler。具体的某种类型的事件处理器。




组件之间的交互如下：
{% asset_img reactor_components.png "reactor组件" %}

时序图如下：
{% asset_img reactor_sequence_diagram.png "reactor时序图" %}

# 3种reactor模式

## Reactor单线程模型

{% asset_img reactor_single_thread.png "reactor 单线程" %}
对应NioEventLoop。所有的I/O操作都在同一个NIO线程上面完成。这个NIO线程，负责了和client建立连接，处理读写请求。

问题
- 单个NIO线程不可靠。如果该IO线程挂了，那么就全挂了。
- 单个NIO线程的处理能力有限，即使该NIO线程100% cpu，也没有发挥多核cpu的资源。读取、解码、编码、发送跟不上。
- 单个IO线程处理过载后，导致新的请求等待(so_backlog队列)，然后不能被accept、不能建立连接，然后又重新发送请求，加剧NIO线程负载。

## Reactor多线程模型

{% asset_img reactor_multithread.png "reactor 多线程" %}

- 一个专门的NIO线程，负责和client建立连接（acceptor线程）。
- 专用的NIO线程池，负责IO读写操作。一个NIO线程可以处理多个链路，但是一个链路由一个NIO线程处理，避免发生竞争问题。 1个connection=1个channel=1个thread（解决并发的线程安全问题）

这种模式能够适合大多数场景了。但是在极高的并发下，单个acceptor线程成为了瓶颈。尤其是在建立连接的时候执行耗时的操作，比如鉴权。


## 主从Reactor多线程模型 

{% asset_img reactor_main_sub.png "reactor 主从模式" %}

对应netty的NioEventLoopGroup。
NIO线程池+acceptor线程池。
acceptor线程池，处理客户端连接。

特点
- acceptor线程池中的一个线程被指派监听端口。
- 监听线程接收客户端请求，建立SocketChannel，并且注册到acceptor线程池的其他线程上，完成认证等耗时的操作。
- 认证等操作通过后，该SocketChannel从acceptor线程上取消注册，再注册到IO线程池上完成后续操作。

# reactor场景分析

reactor的事件驱动模型，适合大量并发的、处理时间短的请求。一旦单个请求处理事件长，将会整体导致性能急剧下降。
像文件传输这样的场景就不适合使用reactor模式，传统的thread per connection更为合适。

# 对比生产者-消费者模式

生产者--消费者模式用queue去缓冲消息。消费者主动pull来获取消息。
reactor模式没有queue。synchronous demultiplexer收到event后立即分发。

# 小结

Reactor模式：
- 适用场景：处理大量小数据量、耗时少的请求
- 哪些组件（synchronous demultiplexer，handle，dispatcher，event handler）
- 核心：1个connection=1个channel=1个thread，没有锁，顺序执行
- 优点（少量线程；分离关注点；事件驱动）
- 缺点（io模型复杂了）
- 多个变种（单NIO线程；多NIO线程；多acceptor）


# 参考资料

- [reactor-siemens.pdf](http://www.dre.vanderbilt.edu/~schmidt/PDF/reactor-siemens.pdf)
- [java使用netty的模型总结](https://www.cnblogs.com/ydymz/p/10219637.html)


