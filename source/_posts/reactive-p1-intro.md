---
title: 反应式编程系列1：简介
date: 2020-11-27 10:51:42
tags: [reactive, 反应式编程]
categories: [反应式编程]
keywords:
description: 反应式编程简介。
---

project reactor官网（[Introduction to Reactive Programming](https://projectreactor.io/docs/core/release/reference/#intro-reactive)）的笔记整理。
<!-- more -->

# what

wiki百科对于反应式编程的描述：
>Reactive programming is an asynchronous programming paradigm concerned with data streams and the propagation of change. This means that it becomes possible to express static (e.g. arrays) or dynamic (e.g. event emitters) data streams with ease via the employed programming language(s).

反应式编程 (reactive programming) 是一种基于数据流 (data stream) 和 变化传递 (propagation of change) 的声明式 (declarative) 的编程范式。

划重点：
- 异步编程
- 数据流
- 变化传递

反应式编程通常使用Observer设计模式实现。

reactive streams模式和Iterator设计模式类似，但是Iterator是pull-based，reactive streams是push-based。

和反应式编程相对应的是命令式（imperative）编程。
以Iterator为例，在命令式编程，开发者明确指令何时从序列中读取数据，以及在精确的控制流中如何处理数据。

在反应式编程中，与之对应的是Publisher-Subscriber。
Publisher通知Subscriber新产生的值。“push”这个动作是“reactive”的关键。另外，计算逻辑以声明式（declarative）方式描述（TODO）。

除了push，反应式编程还提供异常处理、完成通知等aspect。error-handling和completion都会终止流。


# why

阻塞式编程方式容易编写代码，但是停等（stop-wait）的工作方式很浪费性能。
要提升程序性能：
- 并发，使用更多线程、更多硬件资源
- 提高当前资源的使用效率

hmm，异步、非阻塞代码又是有挑战的。
>By writing asynchronous, non-blocking code, you let the execution switch to another active task that uses the same underlying resources and later comes back to the current process when the asynchronous processing has finished.

JVM提供2种异步模型：
- Callbacks： 不会返回value，但是要求一个额外的callback参数（lambda或者匿名类）。
- Futures： 立即返回`Future<T>`。但是value不是立即可用，要等计算结束才能访问。

Callback很难组合，很容易导致callback地狱。
```java
userService.getFavorites(userId, new Callback<List<String>>() { 
  public void onSuccess(List<String> list) { 
    if (list.isEmpty()) { 
      suggestionService.getSuggestions(new Callback<List<Favorite>>() {
        public void onSuccess(List<Favorite> list) { 
          UiUtils.submitOnUiThread(() -> { 
            list.stream()
                .limit(5)
                .forEach(uiList::show); 
            });
        }

        public void onError(Throwable error) { 
          UiUtils.errorPopup(error);
        }
      });
    } else {
      list.stream() 
          .limit(5)
          .forEach(favId -> favoriteService.getDetails(favId, 
            new Callback<Favorite>() {
              public void onSuccess(Favorite details) {
                UiUtils.submitOnUiThread(() -> uiList.show(details));
              }

              public void onError(Throwable error) {
                UiUtils.errorPopup(error);
              }
            }
          ));
    }
  }

  public void onError(Throwable error) {
    UiUtils.errorPopup(error);
  }
});
```

上面例子，使用reactor改写的反应式代码：
```java
userService.getFavorites(userId) 
           .flatMap(favoriteService::getDetails) 
           .switchIfEmpty(suggestionService.getSuggestions()) 
           .take(5) 
           .publishOn(UiUtils.uiThreadScheduler()) 
           .subscribe(uiList::show, UiUtils::errorPopup); 
```


Future要比callback好一点，但是不能很好完成组合（虽然java8引入了CompletableFuture）。

```java
CompletableFuture<List<String>> ids = ifhIds(); 

CompletableFuture<List<String>> result = ids.thenComposeAsync(l -> { 
	Stream<CompletableFuture<String>> zip =
			l.stream().map(i -> { 
				CompletableFuture<String> nameTask = ifhName(i); 
				CompletableFuture<Integer> statTask = ifhStat(i); 

				return nameTask.thenCombineAsync(statTask, (name, stat) -> "Name " + name + " has stats " + stat); 
			});
	List<CompletableFuture<String>> combinationList = zip.collect(Collectors.toList()); 
	CompletableFuture<String>[] combinationArray = combinationList.toArray(new CompletableFuture[combinationList.size()]);

	CompletableFuture<Void> allDone = CompletableFuture.allOf(combinationArray); 
	return allDone.thenApply(v -> combinationList.stream()
			.map(CompletableFuture::join) 
			.collect(Collectors.toList()));
});

List<String> results = result.join(); 
assertThat(results).contains(
		"Name NameJoe has stats 103",
		"Name NameBart has stats 104",
		"Name NameHenry has stats 105",
		"Name NameNicole has stats 106",
		"Name NameABSLAJNFOAJNFOANFANSF has stats 121");
```

使用reactor改写:
```java
Flux<String> ids = ifhrIds(); 

Flux<String> combinations =
		ids.flatMap(id -> { 
			Mono<String> nameTask = ifhrName(id); 
			Mono<Integer> statTask = ifhrStat(id); 

			return nameTask.zipWith(statTask, 
					(name, stat) -> "Name " + name + " has stats " + stat);
		});

Mono<List<String>> result = combinations.collectList(); 

List<String> results = result.block(); 
assertThat(results).containsExactly( 
		"Name NameJoe has stats 103",
		"Name NameBart has stats 104",
		"Name NameHenry has stats 105",
		"Name NameNicole has stats 106",
		"Name NameABSLAJNFOAJNFOANFANSF has stats 121"
);
```



从命令式转变为反应式，有以下好处：
- 组合性（composability）和可读性增强
- 把数组作为流（Data as a flow），并且使用一系列丰富的操作符
- Nothing happens until you subscribe
- 背压（Backpressure）机制，消费者通知生产者发送速率过高
- 高层抽象，屏蔽了底层并发的复杂性

“composability”是指编排多个异步任务，并且使用前面异步任务的结果作为后面任务的输入。
>By “composability”, we mean the ability to orchestrate multiple asynchronous tasks, in which we use results from previous tasks to feed input to subsequent ones. Alternatively, we can run several tasks in a fork-join style

后续文章再深入讨论。

