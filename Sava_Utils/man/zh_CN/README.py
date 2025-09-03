README = r"""
# Srt-AI-Voice-Assistant
### 本项目可利用多个AI-TTS为你的字幕或文本文件配音。<br>并提供包括字幕识别、翻译在内的多种便捷的辅助功能。

### [没有N卡？不会配置环境？点此部署一键启动镜像](https://www.compshare.cn/images/273f6315-2a1d-404d-930b-2e3ea23c163e?referral_code=IHlncJt4RcQDdxKLEZ6pAY&ytag=GPU_yy_sljxjh0616)
如遇到bug或者有什么建议，可以在 [Issues](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/issues) 上反馈  

## 特性
- ✅ 代码开源，界面友好，本地运行，可局域网访问
- ✅ 支持多个TTS项目：BV2,GSV,CosyVoice2,AzureTTS，以及你可以自定义API!
- ✅ 保存个性化设置和预设
- ✅ 批量模式
- ✅ 字幕编辑
- ✅ 字幕批量翻译
- ✅ 单句重新抽卡
- ✅ 支持多角色配音
- ✅ 字幕重新导出
- ✅ 扩展功能：音视频字幕转录
- ✅ I18n

## 安装和启动
### 用源码运行
```
git clone https://github.com/YYuX-1145/Srt-AI-Voice-Assistant.git
cd Srt-AI-Voice-Assistant/
pip install -r requirements.txt
python Srt-AI-Voice-Assistant.py
```
### 可选命令行启动参数
你可以用它自定义启动行为:
|   参数      |     描述           |
|   -----           |       -----               |
| `-p`              | 指定启动端口   |
| `--lan`           | 启用局域网访问         |
| `--no_ext`        | 禁用全部扩展   |
| `--share`         | Create a publicly shareable link for the gradio app.（Colab可能有用） |
| `--server_mode`   | 启用服务模式     |

**然后自己准备配置TTS引擎。Windows用户可以下载打包版或使用搭配GPT-SoVITS的整合包**

**如果本项目不支持你需要的TTS项目，你可以参阅这个[文档](/docs/zh_CN/extension_dev.md)写插件。**

---

## [仅下载本体（打包版）](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/releases)
* 当依赖冲突或无法正常安装时使用此版本


## [下载配合GPT-SoVITS的整合包(Hugging Face)](https://huggingface.co/YYuX/GPT-SoVITS-SAVA-windows-package/tree/main)
* 整合包内预装打包版本体，内置模型不删减，训练和推理代码和官方仓库一致
* 注意：包内自带的程序可能不是最新版本，覆盖掉以完成更新  
"""
