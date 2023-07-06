---
title: sd项目重构实践
date: 2019-06-15 10:55:40
tags: [java, SD项目, 重构]
categories: SD项目
keywords: [重构]
description: 项目快速迭代之后需要重构。首先面临的是服务级别的拆分重构，其次是优化领域模型。在代码级别重构，使用工厂模式、策略模式、更新协议字段、控制单个方法大小等方法。
---

项目从快速原型发展到堆积完基础功能、有一定用户基础。开始还技术的债。重构的价值在这个阶段开始体现。
<!-- more -->
# 服务拆分重构

这个项目会是微服务架构模式，但是一开始就拆分出很多一堆服务，并不是很好的实践：
1. 项目启动初期，业务方向、业务形态变化大，产品需要的快速原型、快速试错。
2. 3个人拆20个微服务，没有实际的价值，只会增加协议变更成本、部署成本，不利于业务的快速试错。

因此，项目初期，只拆分出2个大粒度的核心服务：房间服务和推荐服务。其中房间服务包含个人练歌、唱歌pk游戏房间、Channel鉴权服务。
随着几个月的业务迭代，原来个人练歌功能业务地位提升，代码也越来越复杂。唱歌pk房间的玩法也从单一的小房间轮唱模式，发展为抢唱、轮唱、小房间、大房间。这时候做服务拆分重构：
1. 个人练歌服务
2. 小房间服务
3. 大房间服务
4. Channel鉴权服务

这里有个技巧。个人服务和鉴权服务，一开始就被识别为有可能晋升为单独服务部署和管理，因此作为单独一个domain处理，相关的代码在同一个package。到了要做服务拆分就直接整个package拷贝出来再修改。类似：
```
com.xxx.sd.solo.service
com.xxx.sd.solo.controller
com.xxx.sd.solo.repository
com.xxx.sd.solo.domain
com.xxx.sd.solo.util
```

# 领域模型优化

领域模型是随需求迭代而不断进化的。
最大变化是歌曲片段。最初模型参照竞品修改得来，考虑到schema可能频繁变更，底层采用ElasticSearch存储。业务迭代几个月过后，一堆透传字段、无效字段、非必要字段，导致结构体迅速膨胀，配置和解析踩过几次坑导致服务不可用。于是进行梳理：
1. 过时无效字段，删除
2. 命名不规范、有歧义的字段，先增加新的规范字段，原有服务切换到新字段并且通过验证后，再删除旧字段。
3. 调整节点结构，重新抽象公共属性。

# 代码重构

剩下就是体力活时间，举几个例子。

## 工厂模式

最初只有小房间模式、轮唱玩法（对应game_type字段），房间状态机服务直接根据上下文闭包构造引擎。
后来分别增加抢唱玩法、大房间模式，原来的调用方自己判断要game_type字端选择状态机引擎，显然不合适。

```java
@Service
public class RoomStateEngineFactory implements IStateMachine{

	@Autowired
	private InTurnRoomStateEngine inTurnRoomStateEngine;
	
	@Autowired
	private RaceRoomStateEngine raceRoomStateEngine;

	public IStateMachine newInstance(GameTypeEnum gameType, RoomContext roomContext){
		if(gameType == GameType.IN_TURN){
			return inTurnRoomStateEngine.newInstance(roomContext);
		}
		if(gameType == GameType.RACE){
			return raceRoomStateEngine.newInstance(roomContext);
		}
		
		throw new IllegalArgumentException("unknown gameType="+gameType);
	}
	
	// 其他方法
}
```

不同game_type的状态机实现逻辑，由不同的`IStateMachine`接口实例提供。`RoomStateEngineFactory`作为工厂类，封装选择`IStateMachine`逻辑，调用方无需理解细节。
后续增加新的玩法（game_type），已有的调用方不需要改动。

## 策略模式和if...else...

延长播放时间有多种策略可以选择，随机增加、等值增加、区间增加等，有配置项控制。

```java
if("random".equals(type)){
	// 
}else if("interval".equals(type)){
	//
}else if("range".equals(type)){
	//
}else {
	// unknown config, throws error
}
```

未来还想增加，于是重构为
```java
public interface IExtraTimeStrategy{
	int calculate(int like);
}

public class ExtraTimeStrategyProcessor implements IExtraTimeStrategy, ApplicationContextAware {

	@Value("extraTime.strategy")
	private String strategy;

	// Spring应用上下文环境
	private ApplicationContext applicationContext;
	
	public void setApplicationContext(ApplicationContext applicationContext) {
		this.applicationContext = applicationContext;
	}
	
	public int calculate(int like){
		IExtraTimeStrategy s = applicationContext.getBean("strategy", IExtraTimeStrategy.class);
		if(s==null){
			throw new IllegalArgumentException("unkown strategy="+strategy);
		}
		return s.calculate(like);
	}
}

// 具体的延长时间策略实现类
@Service("byRandom")
public class RandomExtraTimeStrategy implements IExtraTimeStrategy{
	// more code
}

@Service("byInterval")
public class IntervalExtraTimeStrategy implements IExtraTimeStrategy{
	// more code
}

@Service("byRange")
public class RangeExtraTimeStrategy implements IExtraTimeStrategy{
	// more code
}
```

为了新增策略不修改代码，直接向`ExtraTimeStrategyProcessor`注入`ApplicationContext`，根据配置项获取对应策略的bean。

## 方法太长

善用idea的Extract Method功能。

## 修改缓存key

有的缓存已经不再使用，或者需要重命名。
应用使用的缓存key名，都被封装到`RedisKeyHelper`，并且对外提供`getXXXKey([param])`。缓存key重构就只需要更改单一入口。

以前踩过的坑是，同一个缓存key没有集中管理的地方，调用方自己拼接，修改的时候出故障。因此项目一开始就强制规定`RedisKeyHelper`管理所有缓存key。

## api接口字段变更

api中旧的字段在新版本废弃。对应字段加上`@Deprecated`注解，等待3到4星期客户端流量下降到足够低之后，再从代码中删除。




