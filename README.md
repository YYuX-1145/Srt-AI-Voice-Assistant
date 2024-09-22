# Srt-AI-Voice-Assistant
## `Srt-AI-Voice-Assistant`是一个便捷的，通过API调用Bert-VITS2(HiyoriUI)/GPT-SoVITS/微软TTS(在线)为上传的.srt字幕文件生成音频的工具。
当前的代码不够完善，如遇到bug或者有什么建议，可以在 https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/issues 上反馈  

240922更新：<br>
1.增加自定义API功能，但务必注意安全问题！

240821更新：<br>
1.增加对微软在线TTS支持，使用前请配置密钥  
2.部分细节优化

240811更新：<br>
[请注意]：请务必安装依赖，否则会导致无法使用！对于GPT-SoVITS-v2-240807，由于fi分支还没有更新，可以在程序内启动功能受限的api（v1）。  
1.增加错误提示  
2.自动检测项目路径  
3.再次兼容api-v1(但部分参数调整和功能受限)，请在本程序内启动API服务以识别降级后的版本。  
4.重大功能更新：支持重新抽卡合成

240404：<br>
~~[请注意]：fast-inference分支的API已经更新(https://github.com/RVC-Boss/GPT-SoVITS/pull/923) 不更新会导致无法使用~~


240316功能更新：  
1.支持启动API服务，请在设置中填写并保存  
2.支持GSV模型切换（*重要！你可能需要拉取代码更新api.py）  
3.支持保存GSV提示音频和模型预设  

240311修复更新：  
1.offset可以为负值  
2.部分函数改为传不定参（可能有疏忽产生bug，要即时反馈，也可使用0308旧版），为接下来的新功能做准备  
