---
title: travis ci部署github和gitee码云
date: 2019-08-05 15:18:24
tags: [travis ci, devops, 技巧, travis]
categories: [devops]
keywords: [travis 部署 gitee, openssl aes 加密, travis ssh, hexo 部署 码云]
description: 使用travis部署gitee和github，用openssl aes加密ssh私钥后提交到仓库。密码提交到travis保管。travis.yml解密私钥之后用ssh-add加载。hexo deploy增加仓库地址。最后用hexo d部署。
---

博客使用GitHub Pages服务部署，国内访问比较慢，于是考虑部署一份在国内。目标是一次构建，自动部署2份。
于是开始了折腾之旅。

# 选型

最初考虑使用coding.net的pages服务，速度很快，但是试用下来有个问题：coding的默认域名，不提供顶级项目访问。导致Github生成的目录路径直接部署在coding.net会报错。这个问题可以解决，使用自己的域名指向coding提供的默认域名即可。但是coding会对自定义域名的pages进行流量挟持，放广告。不太想用了。

后来发现gitee码云也提供pages服务，并且支持顶级项目访问路径。速度还好，于是就选定了。

# travis入坑

travis是一个自动化构建和部署平台。支持GitHub。要注意的是，travis.org支持public项目，travis.com支持private项目。
使用travis之后有2个好处：
- 在线修改md文件，直接提交就生效。改个做别字什么的好方便了。
- 可以本地提交md文件，远程生成博客。以后文章变多之后，部署就相当方便。

## 使用token部署

travis和github通过Github Token集成，网上查一下就有。（因为最终版本没有使用GitHub Token，所以这里不展开了）
参照[用TravisCI持续集成自动部署Hexo博客的个人实践](https://mtianyan.gitee.io/post/90a759d5.html)，成功集成了GitHub构建。

**于是在gitee申请token，选择了部署权限，给travis调用，但是发现不能部署！** 坑爹了。
这要改变思路。部署静态博客，本质是把生成的静态页文件push到指定分支。以前本地hexo deploy就可以了，但是travis的机器没有ssh key安装，不能直接访问。问题就变成，把一个授权的ssh key安装到travis。

## ssh key安装

首先，要单独一个ssh key用于部署，不要偷懒使用个人电脑的ssh key。
ssh key分为公钥和私钥。用ssh-keygen工具生成，这里不输入密码（passphrase）
```
ssh-keygen -t rsa -f travis.key
```
travis.key是私钥，travis.key.pub是公钥。把公钥分别添加到Github和gitee。

要让travis能够ssh到github和gitee，现在还需要把私钥安装到travis部署脚本。但是私钥是敏感数据，不应该使用明文存储到仓库。因此要对私钥文件做加密，再在部署脚本解密并且安装。

网上提供的方式是travis client，但是这货需要ruby运行时，在服务器折腾安装ruby遇到各种问题，最后放弃了。
加密的话使用openssl就可以了。`-k`是指定密码。然后把密码放到travis管理就好啦。
```
# 加密
openssl aes-256-cfb -in travis.key -out travis.key.enc -k CtbBnkohJFSW27ga 
# 解密
openssl aes-256-cfb -in travis.key.enc -out travis.key.out  -k CtbBnkohJFSW27ga -d 
```
但是在这里掉坑了！

把加密文件丢到travis，解密，执行ssh-add就会提示输入密码（passphrase）。
一开始没有思考为什么会提示输入密码的原因，还以为是添加新key都要的。于是网上试了好几种方式，怎么不用输入passphrase。但是依然部署失败。
就这样折腾了半天，有点绝望。

冷静一下，网上travis安装ssh成功的例子，都没有提到过passphrase的问题。ssh-add认为这个key是加解密了，但是ssh-keygen的时候明明没有输入密码啊。
在`travis.yml`解密后直接打印ids_rsa
```
cat ~./.ssh/id_rsa
```
一堆乱码！解密失败了。

在服务器上检查，上面的命令可以解密成功的。但是放到travis上就有问题了。
检查openssl version，都是1.1.1，应该不是这个问题。
后来再对比网上的aes加密模式，发现别人用的是cbc，我用cfb，修改了之后，发现可以解密了。。。不太明白其中的问题😥，以后再填aes知识的坑。修改后的加密解密
```
# 加密
openssl aes-256-cbc -in travis.key -out travis.key.enc -k CtbBnkohJFSW27ga 
# 解密
openssl aes-256-cbc -in travis.key.enc -out travis.key.out  -k CtbBnkohJFSW27ga -d 
```

# travis.yml

这是我最后测试成功的配置
```yml
language: node_js  #设置语言

dist: bionic

node_js: 10

cache:
    apt: true
    directories:
        - node_modules # 缓存不经常更改的内容

before_install:
  - export TZ='Asia/Shanghai' # 更改时区
  - gunzip .travis/travis.key.enc.gz
  - openssl aes-256-cbc -in .travis/travis.key.enc -out ~/.ssh/id_rsa -d -k ${SSH_PWD} 
  - chmod 600 ~/.ssh/id_rsa
  - eval $(ssh-agent -s)
  - ssh-add
  - git config --global user.name 'ycwu314'
  - git config --global user.email 'ycwu314@foxmail.com'

install:
  - pwd
  - npm install -g hexo --save
  - npm install

script:
  - hexo clean
  - hexo g
  - hexo d

branches:
  only:
    - hexo  

env:
 global:

addons:
  ssh_known_hosts:
    - gitee.com
    - github.com
```

1. 项目的根目录新建了`.travis`目录、`.travis.yml`文件。
2. 把加密后的私钥放到`.travis`目录，对称加密的密钥`${SSH_PWD}`由travis保管即可。
3. 解压缩后的私钥放到`~/.ssh/id_rsa`，访问权限至少为600（ssh踩过好几次坑了）。然后ssh-add加载私钥。
4. ssh首次连接的时候，会提示是否保存公钥。这里addons.ssh_known_hosts插件自动把域名加到known_hosts。
5. 这下连GitHub token也不需要使用了，直接`hexo d`搞定。

# hexo _config.yml配置

hexo部署支持多种方式
```yml
deploy:
- type: git
  repo: git@gitee.com:ycwu314/ycwu314.git
  branch: master
- type: git
  repo: git@github.com:ycwu314/ycwu314.github.io.git
  branch: master
```

# 其他问题

这里有点小问题，`_config.yml`配置的`url`填了`https://ycwu314.github.io`，会影响生成的sitemap和版权声明链接。
也可以在travis上sed为`https://ycwu314.gitee.io`，再部署到码云。不过暂时不折腾了。
后来才发现，gitee非Pro的Pages需要手动部署。。。不过应该可以写脚本解决，模拟登录后点击更新按钮。以后再填坑。

# 小结

- 使用travis部署GitHub Pages很简单，配置GitHub Token就可以了。
- 部署gitee的话，由于gitee token不能正常部署，要使用ssh方式提交。私钥要加密后才能提交仓库。
- travis client可以加密ssh私钥，但是需要ruby运行时，可以直接使用openssl加密。
- travis安装私钥后，使用`hexo d`即像本地一样部署

# 参考资料

- [用TravisCI持续集成自动部署Hexo博客的个人实践](https://mtianyan.gitee.io/post/90a759d5.html)
- [使用Github，Travis CI自动布署Hexo博客到Coding，OSChina服务器](https://www.xn--7qv19ae78e.cn/2017/08/19/2017-08-19-use-travis-ci-push-hexo-blog/)
