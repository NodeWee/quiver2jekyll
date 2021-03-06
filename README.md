# Quiver2Jekyll

将 Quiver 笔记（.qvnote） 转换为 Jekyll 文章（.md）

## 介绍

开发初衷：  
我用 Quiver 记录/书写知识笔记，分享方式是发布到个人网站。网站是托管在 GitHub Pages，使用 Jekyll 生成静态内容。为了自动化从 Quiver 笔记到文章静态网页的流程，节省时间和精力而专注在知识内容本身，诞生了写个转换工具的念头。

> · [Quiver](http://happenapps.com/#quiver) 是一款适合软件开发者使用笔记软件  
> · Jekyll 是 Github Pages 使用的静态站点生成器

> 虽然在 GitHub 上发现了 [zxteloiv](https://github.com/zxteloiv/) 写的 [quiver2jekyll](https://github.com/zxteloiv/quiver2jekyll)，不过功能不能满足我的需求。借鉴了其思路，重头开发，以实现较为完善的功能。


## 支持的功能/特性

- 支持按单篇笔记（.qvnote）、笔记本（.qvnotebook）或笔记库（.qvlibrary）进行转换  
- 支持内链的处理：
	- 图片和文件内链（quiver-image-url，quiver-file-url）自动转换  
	- **笔记内链**（quiver-note-url）自动转换  
	- App URL Scheme（x-callback-url）自动删除  
- 自动转换不兼容的 Makrdown 语法，以适应 kramdown  
- 支持单个笔记本设置项
  - 指定笔记本名称（即博文的分类路径）
  - 标记为草稿状态，不转换
- 支持单篇笔记设置项
  - 指定导出的 markdown 文件名（即博文的 url）
  - 指定 Description（有助于 SEO）
  - 标记为草稿状态，不转换
- 支持自定义 markdown 模版


## 安装
下载本 [repo](https://github.com/nodewee/quiver2jekyll/archive/master.zip)，解压缩。


## 如何使用

命令行：  
`python quiver2jekyll/app/main.py in_path out_path`

⚠️注意：暂时只支持 Python 3

### 举例：  

假设 repo 解压缩后的路径是：`~/Desktop/quiver2jekyll`  

◉ 先打开 quiver2jekyll 所在路径  
```
cd ~/Desktop/quiver2jekyll
```

◉ 查看命令帮助  
```
python app/main.py -h
```


◉ 转换一个笔记库（.qvlibrary）
```
python app/main.py example/example.qvlibrary example/result/one_library
```

◉ 转换一个笔记本（.qvnotebook）
```
python app/main.py example/example.qvlibrary/6412344C-12EB-4281-8E13-B1FCF4CD5F88.qvnotebook example/result/one_notebook
```

◉ 使用 `-t` 参数指定模板  

默认使用的 markdown 模版是 template/post.md。也可以指定一个模板文件，例如
```
python app/main.py example/example.qvlibrary example/result -t path_of_my_markdown.md
```

自定义模板，支持这些变量：  

`{title}` 笔记标题，  
`{uuid}` 笔记 UUID，  
`{tags}` 笔记标签，  
`{content}` 笔记正文，  
`{created}` 笔记创建时间，  
`{updated}` 笔记更新时间  
`{more_matters}` 更多自定义的 front matter 设置项  

◉ 单个笔记本的设置项  
1，标记草稿笔记本  
笔记本的标题前缀下划线“\_”即可。

◉ 使用 `-n` 参数指定笔记本名称（即博文的分类路径）
```
python app/main.py example/example.qvlibrary example/result -n Javascript=web_coding
```
其中名为“Javascript”的笔记本，在导出后其路径是：`example/result/web_coding`。
如果不指定笔记本名称，则使用原笔记本名称，即：`example/result/Javascript`


◉ 单篇笔记的设置项
Quiver 笔记的第一个 cell 选择 markdown 格式，然后按照如下参数格式进行配置。  
1，指定导出的 markdown 文件名（即博文的 url）  
```
<-- config
mdft:the-post-markdown-file-title
-->
```
该条笔记导出后的文件名是：`2020-01-17-the-post-markdown-file-title.md`  
2，添加更多 jekyll markdown 文件 front matter 的配置参数。每行一个

```
<-- config
desc:这里是本文的描述或摘要
toc:true
-->
```
3，标记草稿笔记，转换时将跳过  
笔记的标题前缀下划线“\_”即可。例如：`_note-title`  

可参考 example.qvlibrary



## 开源许可

基于 [Apache License 2.0](/LICENSE.txt) 条款授权。使用本项目代码时需要保留或标明版权信息。



