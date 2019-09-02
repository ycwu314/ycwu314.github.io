---
title: 反爬虫系列之4：重命名图片
date: 2019-09-02 15:32:56
tags: [爬虫, hexo]
categories: [爬虫]
keywords:
description:
---

# 重命名图片

上次提到图片保护的问题
- {% post_link anti-crawler-part-3-image %}

但是8月份才开始使用hexo-lazyload-image插件，导致之前的图片链接被爬了。如果爬虫站点自己保存一份图片，也就算了，否则会一直使用原来的图片地址。
因此要全量更新图片地址了。

更新图片地址，最大影响是图片爬虫。google的图片爬虫更新比较久，旧的失效图片url要经过一段时间才会被去除索引。但因为不是图片站点，这点影响可以忽略。
<!-- more -->

# hexo全量重命名文章图片

hexo项目的_config.yml提供了一个选项
```yml
post_asset_folder: true
```
开启之后，每个文章都有资源文件夹。我在里面存放图片。
并且在文章中使用插入图片。
```
{% asset_img img [title] %}
```

重命名图片，工作有：
- 设计新图片名字的命名规范
- 遍历每个文章的资源文件夹，找到图片列表
- 对于有图片的文章，找到对应的markdown文件，然后重命名引用图片
- 保存修改后的markdown文件
- 重命名图片

命名规范是修改前缀，`v1_`、`v2_`，这样匹配最简单，以后也方便再次重命名。

是一次性修改图片后，提交到git，还是每次构建之前先做重命名呢？
显然前者最高效。但是会导致原来md文件看起来有点别扭。还是交给travis ci干活好了。

附上我的脚本
```python
import os
import sys

# author by ycwu314
# ATTENTION:  change these before start the script
OLD_VERSION_PREFIX = ''
NEW_VERSION_PREFIX = 'v1_'


def img_rename(path):
    if not path:
        return

    if not os.path.isdir(path):
        return

    folders = [path + '/' + f for f in os.listdir(path) if os.path.isdir(path + '/' + f)]
    for folder in folders:
        imgs = [x for x in os.listdir(folder)]
        if len(imgs) == 0:
            continue

        md_file = folder + '.md'
        processed_lines = []
        # key: old_img ; value: new_img
        img_map = {}
        with open(md_file, 'r', encoding='UTF-8') as r:
            for line in r.readlines():
                new_line = line
                for img in imgs:
                    if line.find('asset_img') > -1 and line.find(img) > -1:
                        new_img = get_new_img(img)
                        new_line = line.replace(img, new_img)
                        img_map[img] = new_img
                        continue

                processed_lines.append(new_line)

        with open(md_file, 'w', encoding='UTF-8') as r:
            r.writelines(processed_lines)
            r.flush()

        for img, new_img in img_map.items():
            os.rename(folder + '/' + img, folder + '/' + new_img)


def get_new_img(img: str):
    if img.find(OLD_VERSION_PREFIX) == 0:
        new_img = img.replace(OLD_VERSION_PREFIX, NEW_VERSION_PREFIX, 1)
    else:
        new_img = NEW_VERSION_PREFIX + img

    return new_img


# img_rename(r'C:\workspace\ycwu314.github.io\source\_posts')
if __name__ == '__main__':
    if OLD_VERSION_PREFIX == NEW_VERSION_PREFIX:
        print('error: old version must not be the same as new version')
        sys.exit(-1)

    if len(sys.argv) < 2:
        print('usage: input _posts folder')
        sys.exit(-1)

    input_dir = sys.argv[1]
    print('folder:', input_dir)
    img_rename(input_dir)
```