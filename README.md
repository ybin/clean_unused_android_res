一个Android app资源清理工具
========================

#### 功能
它可以自动清理`.png`、`raw`、`layout`、`anim`、`string`、`array`、`colore`、`dimen`等无用资源。

#### 依赖
该工具用python 3.x写成，它是基于SDK里的lint工具实现的，所以请确保
lint位于系统PATH里。

#### 实现原理
分析`lint --check UnusedResources <app path>`生成的log文件，可删除文件直接删除，如`.png`文件，
xml文件使用正则表达式删除无用的行，如`strings.xml`。

#### TODO

xml节点的`name`属性必须紧跟`tag`之后，如

```
<string name="xxx" translatable="false">XXX</string>
```

而不是

```
<string translatable="false" name="xxx" >XXX</string>
```