# Srt-AI-Voice-Assistant
`Srt-AI-Voice-Assistant`是一个便捷的，通过API本地调用Bert-VITS2-HiyoriUI和GPT-SoVITS或者在线的微软TTS为上传的.srt字幕文件或者.txt纯文本生成音频的工具,亦可以根据合成完毕的音频导出符合音频起止时间的字幕。
如遇到bug或者有什么建议，可以在 https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/issues 上反馈  

## 下载配合GPT-SoVITS的整合包（HF）
* 注意：包内自带的程序现在已经不是最新版本了，覆盖掉以完成更新  
https://huggingface.co/YYuX/GPT-SoVITS-SAVA-windows-package/tree/main

## Todo List
- [x] Multi-speaker synthesis.
- [ ] Multi-language support.
- [x] More comprehensive documentation and user guide.

## 重大的更新历史

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
3.再次兼容api-v1(但部分参数调整和功能受限)，请在本程序内启动API服务以识别降级后的版本。  
4.重大功能更新：支持重新抽卡合成  
