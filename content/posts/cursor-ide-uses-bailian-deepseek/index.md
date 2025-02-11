---
title: "Cursor Ide 使用阿里云百炼 Deepseek 模型"
date: 2025-02-11T14:18:33+08:00
tags: ["AI"]
categories: ["AI"]
description: 
---

阿里云百炼提供DeepSeek-V3和DeepSeek-R1满血版各自提供了高达100万免费tokens的使用额度，有效期6个月。

# 百炼创建子空间

![](1_workspace.png)

# 创建api key

![](2_create_api_key.png)

# 授权deepseek模型访问

![](3_default_workspace_model_plaza.png)

查看然后`查看详情`，最末尾`授权`到子空间。

# 在cursor ide中配置

![](4_cursor_config-models.png)

添加模型：
```
deepseek-r1
deepseek-v3
```

覆盖OpenAI接口地址：
```
https://dashscope.aliyuncs.com/compatible-mode/v1
```

填入百炼授权的api key。

关键的一步：取消选择其他模型。

默认Verify的时候，会使用`gpt4-o`去测试，导致报错。

# 参考

- [DeepSeek全尺寸模型上线阿里云百炼！](https://developer.aliyun.com/article/1651668)
- [Invalid openAI API Key](https://forum.cursor.com/t/invalid-openai-api-key/36401)
