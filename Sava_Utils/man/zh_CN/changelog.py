changelog = r"""
## 重大的更新历史

### V4-2503更新：<br>
#### 为了让版本更具辨识度，除了标注发布日期外，还分配了版本号。 
#### 本次更新后，上一个版本的合成历史和保存的说话人需要重新创建，否则会报错！   
1.字幕编辑  
2.字幕批量翻译  
3.各项细节提升和bug修复  
4.支持CosyVoice2(复用GSV的面板)  
5.(4.0.1)批量模式  
6.(4.1)服务模式  
7.(4.2)I18n  
8.(4.3)新增自动语速和自动去静音功能；现在可从标记文件快速生成多说话人工程  
9.(4.3.1)加入查找和替换；加入一键重新生成按钮

### 250214更新：<br>
1.支持读取历史工程  
2.支持多说话人配音  
3.更完善的文档  

### 250123更新：<br>
1.支持在合成完毕后导出符合实际情况的srt字幕文件，同时也支持通过读取txt纯文本文件来进行合成，在这种情况下会按每句来切分段落。  

2.为了未来的扩展性和简洁性，我不得不放弃了单脚本文件的设计，即使对于下载而言更加方便。代码从现版本逐步开始重构。

3.加入一些文档说明

### 240811更新：<br>
1.增加错误提示  
2.自动检测项目路径  
3.再次兼容api-v1。  
4.重大功能更新：支持重新抽卡合成  
"""
