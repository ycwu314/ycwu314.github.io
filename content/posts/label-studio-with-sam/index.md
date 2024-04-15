---
title: "Label Studio + SAM 半自动标注"
date: 2024-04-15T15:57:24+08:00
tags: ["AI"]
categories: ["AI"]
description: Label Studio + SAM 半自动标注
---

SAM (Segment Anything) ： Meta开源的一个分割模型。

参考这篇文章操作，调整了部分步骤： [OpenMMLab PlayGround：Label-Studio X SAM 半自动化标注](https://github.com/open-mmlab/playground/blob/main/label_anything/readme_zh.md)

label studio + SAM 半自动化标注方案，提供2个能力：
- Point2Labl：用户只需要在物体的区域内点一个点就能得到物体的掩码和边界框标注
- Bbox2Label：用户只需要标注物体的边界框就能生成物体的掩码，社区的用户可以借鉴此方法，提高数据标注的效率。


# 搭建环境

## conda

```
conda create -n rtmdet-sam python=3.9 -y
conda activate rtmdet-sam

git clone https://github.com/open-mmlab/playground

```


## 安装 PyTorch
```
# Linux and Windows CPU only
pip install torch==1.10.1+cpu torchvision==0.11.2+cpu torchaudio==0.10.1 -f https://download.pytorch.org/whl/cpu/torch_stable.html
```

但是在我本地报错：
```
(base) D:\workspace>pip install  torchaudio==0.10.1 -f https://download.pytorch.org/whl/cpu/torch_stable.html
Looking in links: https://download.pytorch.org/whl/cpu/torch_stable.html
ERROR: Could not find a version that satisfies the requirement torchaudio==0.10.1 (from versions: 2.2.0, 2.2.0+cpu, 2.2.1, 2.2.1+cpu, 2.2.2, 2.2.2+cpu)
ERROR: No matching distribution found for torchaudio==0.10.1
```

根据pytorch官网资料，调整为

```
# https://pytorch.org/get-started/previous-versions/

conda install pytorch==1.10.1 torchvision==0.11.2 torchaudio==0.10.1 cpuonly -c pytorch
```

## 安装 SAM 并下载预训练模型

```
cd D:\workspace\playground\label_anything

# 在 Windows 中，进行下一步之前需要完成以下命令行
# conda install pycocotools -c conda-forge 

pip install opencv-python pycocotools matplotlib onnxruntime onnx timm
pip install git+https://github.com/facebookresearch/segment-anything.git
pip install segment-anything-hq

# 下载sam预训练模型
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
# 如果想要分割的效果好请使用 sam_vit_h_4b8939.pth 权重
# wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth
# wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth

# 下载 HQ-SAM 预训练模型
wget https://huggingface.co/lkeab/hq-sam/resolve/main/sam_hq_vit_b.pth
#wget https://huggingface.co/lkeab/hq-sam/resolve/main/sam_hq_vit_h.pth
#wget https://huggingface.co/lkeab/hq-sam/resolve/main/sam_hq_vit_l.pth

# 下载 mobile_sam 预训练模型
wget https://raw.githubusercontent.com/ChaoningZhang/MobileSAM/master/weights/mobile_sam.pt
# 如果下载失败请手动下载https://github.com/ChaoningZhang/MobileSAM/blob/master/weights/ 目录下的mobile_sam.pt,将其放置到path/to/playground/label_anything目录下
```

根据需要下载权重文件，记住路径。

这里使用`mobile_sam.pt`，同时保存到label_anything目录下。

## 安装 Label-Studio 和 label-studio-ml-backend

```
pip install label-studio==1.11.0

# 对接SAM，提供推理服务
# https://github.com/HumanSignal/label-studio-ml-backend

pip install label-studio-ml==1.0.9


# 如果想直接使用 local storage 而非导入：
conda env config vars set LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
conda env config vars set LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=d:\\dataset
```

# 启动应用

这里需要两个conda命令行，一个启动label-studio，另一个启动label-studio-ml。

第一个conda启动label-studio
```
conda activate rtmdet-sam

label-studio start -p 8080 --data-dir d:\\label-studio-data
```

第二个启动label-studio-ml
```
conda activate rtmdet-sam


cd D:\workspace\playground\label_anything

label-studio-ml start sam --port 8003 --with model_name=mobile_sam sam_config=vit_t sam_checkpoint_file=d:\workspace\playground\label_anything\mobile_sam.pt out_mask=True out_bbox=True device=cpu

# device=cuda:0 为使用 GPU 推理，如果使用 cpu 推理，将 cuda:0 替换为 cpu
```

必须进入label anything工作目录，否则启动报错：
>python: can't open file 'D:\workspace\playground\sam\_wsgi.py': [Errno 2] No such file or directory

这里使用mobile_sam + cpu 推理测试。


# 配置标签

根据文章在label studio配置标签。

>其中 KeyPointLabels 为关键点标注，BrushLabels 为 Mask 标注，PolygonLabels 为外接多边形标注，RectangleLabels 为矩形标注。

然后接入label-studio-ml：
![](https://user-images.githubusercontent.com/25839884/233836727-568d56e3-3b32-4599-b0a8-c20f18479a6a.png)


>进入标注任务，需要打开 Auto-Annotation 的开关，并建议勾选 Auto accept annotation suggestions,并点击右侧 Smart 工具，切换到 Point 后，选择下方需要标注的物体标签，这里选择 cat。如果是 BBox 作为提示词请将 Smart 工具切换到 Rectangle。

注意是这2个智能工具激活自动标注。

![](https://user-images.githubusercontent.com/25839884/233833200-a44c9c5f-66a8-491a-b268-ecfb6acd5284.png)


# 结论

使用 mobile_sam + cpu，准确度一般般，速度大概1~3s返回推理结果。

如果图片有些模糊失真，错误就很明显。
