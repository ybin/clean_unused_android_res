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

#### 参考博文

《清理清理Android APP无用资源》： http://ybin.gitcafe.com/2014/12/19/clean-unused-android-app-resource/