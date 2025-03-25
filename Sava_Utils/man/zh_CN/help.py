help = r"""
# 使用指南

## 0.配置和使用服务
#### 本项目可调用2个本地项目：Bert-VITS2、GPT-SoVITS  
#### 和1个在线项目：微软TTS  
* 本地项目只需要在设置页中填写并保存项目和解释器路径，或者**以更简单的方式：将程序放于整合包根目录内即可** ，然后点击第一页右下角对应按钮即可一键启动API服务！
* 对于微软TTS，需要按教程注册账号并将密钥填写在设置页内。请注意每月的免费额度！

## 1.开始使用
### 本项目可以为字幕或者纯文本配音。
* 对于字幕，实际有效的输入只有起始时间。当前一个字幕过长时，后一个字幕将在其后顺延。你可以在设置里设置最小语音间隔。
* 对于纯文本，将按照结束标点符号和换行切割成每一条字幕。
* 完成生成后，可以在编辑页面导出符合音频实际起止时间的字幕。
### A.单一说话人的情形
* 1.在`字幕配音`上半页右侧上传字幕或者纯文本文件。
* 2.在中间选择你的项目，调整参数。
* 3.点击下方的`生成`，等待片刻。
* 4.下载你的音频。

### B.多说话人的情况
* 1.在`字幕配音`上半页右侧上传字幕或者纯文本文件。
* 2.点击左侧文件展示下方的按钮`生成多角色项目`
* 3.创建数个说话人：
  - a.展开位于编辑页最下方的`多角色配音`栏
  - b.选择目标项目
  - c.`在选择/创建说话人`框中，输入说话人的名字
  - d.调整上方对应参数。全部的参数，包括端口号将作为说话人的配置。然后点击`💾`创建说话人。同名的说话人会覆盖。
* 4.在下拉列表里选中你的说话人，然后勾选对应的字幕，再点击下方的`✅`来应用说话人。你将在第4列文本看到说话人信息。
* 5.上一次点击`✅`时选中的说话人会`自动`应用为`默认说话人`(仅多说话人项目生效，未指派说话人的情况下就使用默认说话人)，即使你没有选择任何一条字幕。
* 6.点击`生成多角色配音`，将会开始为所有指定说话人的字幕生成音频
* ⚠️如果你正在使用和创建GSV的说话人时不同的语言，GSV的说话人会无法使用。
* 注：gsv的预设创建同理。在切换预设时，会自动加载模型。

### 如果对某条语音不满意？
* 1.在下半编辑页中通过滑条找到目标字幕
* 2.可以修改文本内容。重新抽卡完成后，字幕内容会存档。
* 3.点击`🔄️`重新生成单条语音。如果你通过单说话人创建工程，在未指派说话人时，参数以当前创建工程所使用的项目的面板为准。若指派了说话人，则按说话人的参数合成。
* 4.通过多说话人创建的工程必须指派说话人。
* 5.点击`重新拼接内容`，重新合成音频。

### C.历史工程的再编辑
* 编辑页上侧栏的合成历史中选择对应工程，然后点击加载。
* 然后应该也不用多说了吧？

### D.字幕编辑
#### 1.复制
* 复制选中的字幕。
#### 2.删除
* 删除选中的字幕。
#### 3.合并
* 你需要至少选择2个字幕作为合并的起点和终点。
* 只有选中字幕的id的最大和最小值作为实际有效输入。
#### 以上更改不会立即存档，因此可以通过重新加载当前工程来撤销操作。

#### 4.更改时间码
* 按srt的时间格式修改字幕的起止时间。
* 必须点击`应用时间`后，本页的时间码才会被保存，并存档。
* 如果在未保存的情况下进行翻页等其他操作，更改将会丢失。

## 2.我遇到了无法解决的错误
### 您需要：
* 详细地描述问题，并指出问题发生前，您做了哪些操作。
* 推荐在评论区和[GitHub-issues](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/issues)反馈。Github-issue的模版会指引您更清晰地反馈问题。
"""
