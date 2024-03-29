---
title: "Linux 的 [] 和 [[]] 区别"
date: 2024-01-11T11:36:05+08:00
tags: ["linux"]
categories: ["linux"] 
description:  "[[]] 是/bin/bash的扩展。[] 适用于大多数shell (如 /bin/sh)。"
---


TLDR：
- `[]`适用于大多数shell。字符串比较的时候，变量要用双引号括住。
- `[[]]`是bash的扩展。字符串比较的时候，变量可以不用双引号括住。支持正则表示、逻辑运算等。

来自poe的整理。

# `[]` vs `[[]]`

1. "[]"（方括号）：方括号是传统的条件测试结构，在大多数Unix和Linux shell中都可用。它们通常用于测试文件属性、字符串比较和数值比较等基本条件。

   示例：
   - 文件存在性的测试：`[ -f filename ]` （如果文件存在且为普通文件，则条件成立）
   - 字符串比较：`[ "$var" == "value" ]` （如果变量var的值等于"value"，则条件成立）

   方括号在条件测试中使用时，需要注意以下几点：
   - 方括号内的测试表达式和运算符之间需要有空格。
   - 方括号的开始和结束需要用空格或其他命令分隔。
   - **方括号内的变量应该用双引号引起来**，以避免空格或特殊字符引起的问题。

2. "[[]]"（双方括号）：双方括号是Bash shell的扩展功能，引入了更强大的条件测试和模式匹配功能。它们提供了更灵活的字符串比较、模式匹配和逻辑运算等高级功能。

   示例：
   - 字符串模式匹配：`[[ $var == pattern ]]` （如果变量var与模式pattern匹配，则条件成立）
   - 正则表达式匹配：`[[ $var =~ regex ]]` （如果变量var与正则表达式regex匹配，则条件成立）

   双方括号在条件测试中使用时，具有以下特点：
   - **双方括号内的变量不需要引号**。
   - 双方括号支持正则表达式匹配（使用`=~`运算符）。
   - 双方括号支持逻辑运算符（如`&&`、`||`）的短路特性。

# 使用例子

## "[]"（方括号）的用法：

   - 文件属性测试：
     - `-e file`：文件存在性测试
     - `-f file`：文件为普通文件测试
     - `-d file`：文件为目录测试
     - `-r file`：文件可读性测试
     - `-w file`：文件可写性测试
     - `-x file`：文件可执行性测试

   - 字符串比较：
     - `string1 = string2`：字符串相等测试（注意等号两侧需要有空格）
     - `string1 != string2`：字符串不等测试
     - `-z string`：字符串为空测试
     - `-n string`：字符串非空测试

   - 数值比较：
     - `num1 -eq num2`：数值相等测试
     - `num1 -ne num2`：数值不等测试
     - `num1 -lt num2`：数值小于测试
     - `num1 -gt num2`：数值大于测试
     - `num1 -le num2`：数值小于等于测试
     - `num1 -ge num2`：数值大于等于测试



## "[[]]"（双方括号）的用法：

   - 字符串比较和模式匹配：
     - `string1 == pattern`：字符串与模式匹配测试
     - `string1 != pattern`：字符串与模式不匹配测试
     - `string =~ regex`：字符串与正则表达式匹配测试

   - 逻辑运算：
     - `expression1 && expression2`：逻辑与运算
     - `expression1 || expression2`：逻辑或运算

   - 高级条件测试：
     - `-o option`：测试选项是否启用
     - `-v var`：变量是否已设置
     - `-n var`：变量非空测试（与"[]" 中的 `-n` 不同）




