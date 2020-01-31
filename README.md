# Quiver2Jekyll

实现将 Quiver 笔记（.qvnote） 转换为 Jekyll 博文（.md）

## 介绍

开发初衷：  
我用 Quiver 记录/书写知识笔记，用 GitHub Pages 发布博文。为了简化发布/分享的流程，节省时间和精力而专注在知识内容本身，诞生了写个转换工具的念头。

> · [Quiver](http://happenapps.com/#quiver) 是一款适合开发者使用笔记软件  
> · Jekyll 是 Github Pages 使用的静态站点生成器

> 虽然在 GitHub 上发现了 [zxteloiv](https://github.com/zxteloiv/) 写的 [quiver2jekyll](https://github.com/zxteloiv/quiver2jekyll)，不过功能不能满足我的需求。借鉴了其思路，重头开发，以实现较为完善的功能。


## 支持的功能/特性

- 输入的文件可以是：笔记（.qvnote）、笔记本（.qvnotebook）或笔记库（.qvlibrary）  
- 支持自定义 markdown 模版
- 支持内链处理：
	- 图片内链（quiver-image-url）自动转换  
	- **笔记内链**（quiver-note-url）自动转换  
	- App URL Scheme (x-callback-url)自动删除  
- 支持指定笔记本名称（即博文的分类路径）
- 支持指定每篇笔记导出的 markdown 文件名（即博文的 url）
- 支持忽略草稿笔记  
- 自动转换一些 Makrdown 语法，以适应 kramdown  
	- 单个换行符号后添加两个空格

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

◉ 使用 `-n` 参数指定笔记本名称（即博文的分类路径）
```
python app/main.py example/example.qvlibrary example/result -n Javascript=web_coding
```
其中名为“Javascript”的笔记本，在导出后其路径是：`example/result/web_coding`。
如果不指定笔记本名称，则使用原笔记本名称，即：`example/result/Javascript`

◉ 自定义每篇笔记导出的 markdown 文件名（即博文的 url）  

Quiver 笔记的第一个 cell 选择 markdown 格式，然后按照如下格式指定笔记的 .md 文件名
```
{jkfn:this-post-s-jekyll-file-name}
```
该条笔记导出后的文件名是：`2020-01-17-this-post-s-jekyll-file-name.md`

可参考 example.qvlibrary


◉ 忽略草稿笔记  
笔记的标题前缀下划线“\_”即可。例如：`_note-title`


## 授权
以 **BSD 3-Clause Clear License** 进行授权。详情请参见 [LICENSE](https://github.com/NodeWee/quiver2jekyll/blob/master/LICENSE) 文件。

## TODO / 欢迎一起协作
- 兼容 Python 2
- 英文版：①代码里的注释添加英文版，②README 的英文版

