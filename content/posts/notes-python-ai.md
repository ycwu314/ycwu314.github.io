---
title: "Python AI 笔记"
date: 2024-03-15T17:16:06+08:00
tags: ["AI"]
categories: ["AI"]
description: 遇到问题的记录。
---

# conda安装

如果安装给所有用户，需要提权，否则在pychram容易出现无权限访问。

最简单是安装给当前用户。

# 安装faiss

```shell
conda install -c pytorch faiss-cpu=1.8.0
```
该命令的目的是从pytorch通道安装faiss-cpu库的1.8.0版本


# pandas版本

```py
data = pd.read_csv(StringIO(res.text), sep='\t', header=None, error_bad_lines=False)

TypeError: read_csv() got an unexpected keyword argument 'error_bad_lines'
```

>Deprecated since version 1.3.0: The on_bad_lines parameter should be used instead to specify behavior upon encountering a bad line instead.

改为
```py
data = pd.read_csv(StringIO(res.text), sep='\t', header=None, on_bad_lines='skip')
```

# windows上的符号链接

>C:\miniconda3\envs\faiss\lib\site-packages\huggingface_hub\file_download.py:149: UserWarning: `huggingface_hub` cache-system uses symlinks by default to efficiently store duplicated files but your machine does not support them in C:\Users\xxxx\.cache\huggingface\hub\models--sentence-transformers--bert-base-nli-mean-tokens. Caching files will still work but in a degraded version that might require more space on your disk. This warning can be disabled by setting the `HF_HUB_DISABLE_SYMLINKS_WARNING` environment variable. For more details, see https://huggingface.co/docs/huggingface_hub/how-to-cache#limitations.
>
>To support symlinks on Windows, you either need to activate Developer Mode or to run Python as an administrator. In order to see activate developer mode, see this article: https://docs.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development
  warnings.warn(message)


参见：
https://huggingface.co/docs/huggingface_hub/v0.21.4/guides/manage-cache#limitations

huggingface的模型，为了减少重复下载，支持使用符号链接去重。

在windows系统，需要开启开发者模式才能支持符号链接。按照 [enable-your-device-for-development](https://docs.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development) 操作



# ipython的`%%time`

```py
%%time

UsageError: %%time is a cell magic, but the cell body is empty. Did you mean the line magic %time (single %)?
```

gpt整理：

`%%time`和`%time`都是IPython中的魔术命令，用于测量代码执行时间，但它们的用法和作用略有不同。

1. **`%%time`**：
   - `%%time`是用于测量整个单元（cell）代码执行的时间。
   - 当你在Jupyter Notebook或IPython中使用`%%time`时，它会测量整个单元中所有代码的执行时间，并且会显示出来。

   ```python
   %%time
   # 这里是你的代码
   ```

2. **`%time`**：
   - `%time`是用于测量单行代码执行的时间。
   - 当你在Jupyter Notebook或IPython中使用`%time`时，它会测量在同一行中直接跟在`%time`后面的那行代码的执行时间，并且会显示出来。

   ```python
   %time your_single_line_code
   ```


