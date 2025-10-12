# Srt-AI-Voice-Assistant
### This project can use multiple AI-TTS to dub for your subtitle or text files.<br>And provides various convenient auxiliary functions including audio/video transcription and subtitle translation.
If you have encountered problems or want to create a feature request, please go to [Issues](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/issues) . 
## Features
- ✅ Open-source, Friendly WebUI interface, Run locally and Accessible via LAN
- ✅ Support multiple TTS projects: BV2, GSV, CosyVoice2, AzureTTS, and you can even customize your APIs!
- ✅ Save personalized settings and presets
- ✅ Batch mode
- ✅ Subtitle editing
- ✅ Subtitle translation
- ✅ Regenerating Specific Lines
- ✅ Support multi-speaker dubbing
- ✅ Re-export subtitles
- ✅ Extended functions: subtitle transcription for audio/video
- ✅ I18n

## Installation
### From Source Code
```
git clone https://github.com/YYuX-1145/Srt-AI-Voice-Assistant.git
cd Srt-AI-Voice-Assistant/
pip install -r requirements.txt
python Srt-AI-Voice-Assistant.py
```
### Optional Command Line Arguments
You can customize the behavior of the application with the following command-line arguments:
|   Arguments       |     Description           |
|   -----           |       -----               |
| `-p`              | Specify the server port   |
| `--lan`           | Enable LAN access         |
| `--no_ext`        | Disable all extensions    |
| `--share`         | Create a publicly shareable link for the gradio app.|
| `--server_mode`   | Activate server mode, which disables all functions that might cause conflicts in multi-user environments.     |

**And then prepare TTS engines yourself. For Windows users, you can download the packaged version or use the integrated package with GPT-SoVITS.**

**If the required TTS engine is not on the supported list, you can refer to the [documentation](/docs/en_US/extension_dev.md) to write an extension.**

---

### [Download the packaged version only](https://github.com/YYuX-1145/Srt-AI-Voice-Assistant/releases)
* Use this version only when there are dependency conflicts or installation issues.

### [Download the integrated package with GPT-SoVITS (From Hugging Face)](https://huggingface.co/YYuX/GPT-SoVITS-SAVA-windows-package/tree/main)
* The GPT-SoVITS integrated package includes the packaged version, without removing any built-in or pretrained models, and its code for finetuning and inference is the same with the official repository.
* **Note:** Packaged Version included in the GPT-SoVITS integrated package may not be the latest version; overwrite it to update.