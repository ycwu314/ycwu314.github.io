---
title: "Pandas Notes"
date: 2024-03-20T10:13:58+08:00
tags: ["AI"]
categories: ["AI"]
description: pandas 学习笔记
---

# jupyter一个cell多个输出

```py
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"
```


# 数据类型

## Series

Series是一个**一维标签数组**，可容纳任何数据类型（整数、字符串、浮点数、Python 对象等）。轴标签统称为索引。


```py
s = pd.Series(data, index=index)

# 传入ndarray
s = pd.Series(np.random.randn(5), index=["a", "b", "c", "d", "e"])

# 传入dict。可以自动获取index
d = {"b": 1, "a": 0, "c": 2}
pd.Series(d)

# 获取Series的底层数据类型
d.dtype

# 获取底层的numpy array
d.to_numpy()

```


## DataFrame


DataFrame 是一种**二维标签**数据结构，其中的列可能具有不同的类型。你可以把它想象成sheet或 SQL table，或者Series对象构成的dict。


```py
d = {
    "one": pd.Series([1.0, 2.0, 3.0], index=["a", "b", "c"]),
    "two": pd.Series([1.0, 2.0, 3.0, 4.0], index=["a", "b", "c", "d"]),
}
df = pd.DataFrame(d)
df
```

```
   one  two
a  1.0  1.0
b  2.0  2.0
c  3.0  3.0
d  NaN  4.0
```

## DataFrame的index和column

- 行索引（index）：行索引是用来标识和访问 DataFrame 中的行的标签。行索引可以是整数、字符串、日期时间等类型。行索引通常是唯一的，但不要求一定唯一。如果没有明确指定行索引，Pandas 会默认使用从 0 开始的整数作为行索引。

- 列索引（column）：列索引用来标识和访问 DataFrame 中的列的标签。每一列都有一个唯一的列索引。列索引通常是字符串，用来描述该列的含义或名称。

```py
df.index
df.column
```


## NaN

NaN (not a number) 表示缺失值。对应于`np.nan`。

相关操作：
- isna() or isnull(): 检查NaN
- dropna()
- fillna()
- replace()

## dtype

`dtype` 在 Pandas 中是用来表示数据类型的属性。Pandas 支持多种数据类型，包括整数、浮点数、字符串、布尔值等。以下是一些常见的 Pandas 数据类型：

- `int64`：64 位整数
- `float64`：64 位浮点数
- `object`：Python 对象类型，通常表示字符串或者混合类型
- `bool`：布尔值
- `datetime64`：日期时间类型
- `timedelta`：表示两个日期时间之间的差值
- `category`：分类数据类型，用于节省内存和提高性能

当你创建一个 Pandas 的 DataFrame 或者 Series 对象时，Pandas 会自动推断数据类型，但你也可以通过参数指定数据类型。例如：

```python
import pandas as pd

# 创建一个 DataFrame，指定列的数据类型
data = {'int_col': [1, 2, 3, 4],
        'float_col': [1.0, 2.0, 3.0, 4.0],
        'str_col': ['a', 'b', 'c', 'd']}
df = pd.DataFrame(data, dtype={'int_col': 'int32', 'float_col': 'float32', 'str_col': 'object'})

# 查看 DataFrame 的数据类型
print(df.dtypes)
```



# 定位

| 方法   | 描述                     | 示例                              |
|--------|--------------------------|----------------------------------|
| loc    | 基于标签的索引，通过行标签和列标签访问数据 | `df.loc['X', 'A']` |
| iloc   | 基于整数位置的索引，通过行号和列号访问数据 | `df.iloc[0, 0]`    |
| at     | 针对单个标量值的快速访问方法 | `df.at['X', 'A']`               |



| Operation                  | Syntax          | Result     |
|----------------------------|-----------------|------------|
| Select column              | df[col]         | Series     |
| Select row by label        | df.loc[label]   | Series     |
| Select row by integer location | df.iloc[loc] | Series     |
| Slice rows                 | df[5:10]        | DataFrame  |
| Select rows by boolean vector | df[bool_vec]  | DataFrame  |

# axis

- axis=0 行方向
- axis=1 列方向

| 操作                         | Series                     | DataFrame                  |
|------------------------------|----------------------------|----------------------------|
| 沿着行的方向进行操作          | `axis=0`，默认值           | `axis=0`                   |
| 沿着列的方向进行操作          | 无，Series 是一维的         | `axis=1`                   |

而在 Series 中，因为 Series 是一维的，所以只有一个轴，即索引轴，因此 axis=0 通常指示沿着索引轴的方向进行操作


# 字符串操作str

当你想要在 Pandas 中对字符串列进行处理时，你可以使用 str 属性来访问一系列字符串方法。

# Categorical 类型

在 Pandas 中，`Categorical` 类型是一种特殊的数据类型，用于表示具有有限个可能取值的数据，并且通常用于节省内存和提高性能。

`Categorical` 类型适用于具有相对较少不同取值的列，例如性别、地区、状态等。将这些数据存储为 `Categorical` 类型可以节省内存，并且在某些情况下可以提高计算效率。

你可以使用 `pd.Categorical()` 来创建 `Categorical` 类型的数据。下面是一个示例：

```python
import pandas as pd

# 创建一个普通的 Series
data = ['apple', 'banana', 'apple', 'banana', 'apple', 'banana']
s = pd.Series(data)

# 将 Series 转换为 Categorical 类型
cat_s = pd.Categorical(s)

# 打印 Categorical 类型的数据
print(cat_s)
```

输出示例：

```
['apple', 'banana', 'apple', 'banana', 'apple', 'banana']
Categories (2, object): ['apple', 'banana']
```

在这个示例中，原始的 Series 包含了水果的名称，将其转换为 `Categorical` 类型后，Pandas 显示了两个不同的类别（'apple' 和 'banana'），并且每个元素都以数字编码的形式存储，从而节省了内存。

# 遍历 Series


```py
import pandas as pd

# 创建一个 Series
s = pd.Series([1, 2, 3, 4, 5])


# 使用迭代器遍历 Series
for item in s:
    print(item)

# 使用 iteritems() 方法遍历 Series
for index, value in s.iteritems():
    print(f'Index: {index}, Value: {value}')

```


# 遍历 DataFrame

```py
import pandas as pd

# 创建一个 DataFrame
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

# 使用 iterrows() 方法遍历 DataFrame
for index, row in df.iterrows():
    print(f'Index: {index}, Row values: {row}')


# 使用 itertuples() 方法遍历 DataFrame
for row in df.itertuples():
    print(row)

```

`itertuples()` 元组的第一个元素将是行的相应索引值，其余的值则是行值。


# 排序

Series、DataFrame支持使用`sort_index()`和`sort_value()`排序。

# concat

Adding a column to a DataFrame is relatively fast. However, adding a row requires a copy, and may be expensive. We recommend passing a pre-built list of records to the DataFrame constructor instead of building a DataFrame by iteratively appending records to it.

```py
df1 = pd.DataFrame({'A': [1, 2, 3],
                    'B': [4, 5, 6]})
df2 = pd.DataFrame({'A': [7, 8, 9],
                    'B': [10, 11, 12]})

# 使用 concat() 方法沿行方向连接两个 DataFrame
# 默认为 axis=0，按照行方向
result = pd.concat([df1, df2])
result
```

|    |   A |   B |
|----|-----|-----|
|  0 |   1 |   4 |
|  0 |   7 |  10 |
|  1 |   2 |   5 |
|  1 |   8 |  11 |
|  2 |   3 |   6 |
|  2 |   9 |  12 |

```py
# axis=1，按照列方向
result = pd.concat([df1, df2], axis=1)
```

|    |   A |   B |   A |   B |
|---:|----:|----:|----:|----:|
|  0 |   1 |   4 |   7 |  10 |
|  1 |   2 |   5 |   8 |  11 |
|  2 |   3 |   6 |   9 |  12 |


# join

```py
left = pd.DataFrame({"key": ["foo", "bar"], "lval": [1, 2]})
right = pd.DataFrame({"key": ["foo", "bar"], "rval": [4, 5]})

# 默认就是inner方式
pd.merge(left,right,on="key", how="inner")
```


|    | key | lval | rval |
|---:|-----|------|------|
|  0 | foo |    1 |    4 |
|  1 | bar |    2 |    5 |

