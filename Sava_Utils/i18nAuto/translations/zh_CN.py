i18n_dict = {
    # functions in main
    "You need to load custom API functions!": "需要加载自定义API函数！",
    "Please upload the subtitle file!": "请上传字幕文件！",
    "The current mode does not allow batch processing!": "当前不允许批量处理！",
    "Synthesizing single-speaker task": "正在合成单说话人任务",
    "All subtitle syntheses have failed, please check the API service!": "所有的字幕合成都出错了，请检查API服务！",
    "Done! Time used": "完成！所用时间",
    "There is no subtitle in the current workspace": "当前没有字幕",
    "Warning: No speaker has been assigned": "警告：没有指派任何说话人",
    "Using default speaker": "当前使用选定的默认说话人",
    "Speaker archive not found": "找不到说话人存档",
    "Synthesizing multi-speaker task, the current speaker is": "正在合成多说话人任务，当前说话人为",
    "Synthesis for the single speaker has failed !": "单一说话人的全部语音合成失败了！",
    "Failed to execute ffmpeg.": "执行ffmpeg命令失败！",
    "Done!": "完成!",
    "Failed subtitle id": "出错字幕id",
    "error message received": "接收的报错信息为",
    "Please go to the settings page to specify the corresponding environment path and do not forget to save it!": "请前往设置页面指定环境路径并保存!",
    " has been launched, please ensure the configuration is correct.": "已启动，请确保其配置文件无误。",
    "API downgraded to v1, functionality is limited.": "API降级至v1，功能受限。",
    "You must specify the speakers while using multi-speaker dubbing!": "使用多角色配音时，必须指定说话人！",
    "Audio re-generation was successful! Click the <Reassemble Audio> button.": "重新合成成功！点击重新拼接内容。",
    "Audio re-generation failed!": "重新合成失败！",
    "Reassemble successfully!": "重新合成完毕！",
    "This function has been disabled!": "当前功能已被禁用！",
    "Please enter a valid name!": "请输入有效的名称！",
    "Saved successfully!": "保存成功!",
    # UI in main
    "Subtitle Dubbing": "字幕配音",
    "File content": "文件内容展示",
    "Speaker Map": "说话人映射表",
    "Original Speaker": "原始说话人",
    "Target Speaker": "映射后的目标说话人",
    "Create Multi-Speaker Dubbing Project": "创建多角色项目",
    "Custom API": "自定义API",
    "Frame rate of Adobe Premiere project, only applicable to csv files exported from Pr": "Pr项目帧速率,仅适用于Pr导出的csv文件",
    "API Launcher": "启动API服务",
    "Number of threads for sending requests": "请求线程数",
    "Voice time offset (seconds)": "语音时间偏移(秒) 延后或提前所有语音的时间",
    "Upload file (Batch mode only supports one speaker at a time)": "上传文件(批量模式只支持单个同一说话人)",
    "Output Info": "输出信息",
    "Output File": "输出文件",
    "Editing area *Note: DO NOT clear temporary files while using this function.": "编辑区域 *Note:请勿在使用本功能时清除临时文件。",
    "History": "合成历史",
    "Load": "加载",
    "Reassemble Audio": "重新拼接",
    "Export Subtitles": "导出字幕",
    "Select All": "全选",
    "Reverse Selection": "反选",
    "Clear Selection": "清除选择",
    "Apply Timestamp modifications": "应用时间码",
    "Copy": "复制",
    "Merge": "合并",
    "Delete": "删除",
    "Multi-speaker dubbing": "多角色配音",
    "Select/Create Speaker": "选定/创建说话人",
    "TTS Project": "说话人所属项目",
    "Start Multi-speaker Synthesizing": "生成多角色配音",
    "Auxiliary Functions": "辅助功能",
    "Extended Contents": "外部扩展内容",
    "Settings": "设置",
    "Readme": "简介",
    "Issues": "常见错误",
    "Help & User guide": "使用指南",
    # utils
    "An error occurred": "出现错误",
    "Server Mode has been enabled!": "服务模式已启用！",
    "Temporary files cleared successfully!": "成功清除临时文件！",
    "There are no temporary files.": "目前没有临时文件！",
    "Execute command": "执行命令",
    "No running processes": "没有运行的进程",
    "Process terminated.": "已终止进程",
    "<Multiple Files>": "<多个文件>",
    "Failed to read file": "读取字幕文件出错",
    "Error: File too large": "错误：文件过大",
    "Unknown format. Please ensure the extension name is correct!": "未知的格式，请确保扩展名正确！",
    "Creating a multi-speaker project can only upload one file at a time!": "创建多角色配音工程只能上传有且只有一个文件！",
    # edit_panel
    "Not available!": "不可用！",
    "Must not be empty!": "不得为空！",
    "No subtitles selected.": "未选中任何字幕",
    "Please select both the start and end points!": "请选择起点和终点！",
    "Input format mismatch": "输入格式不匹配",
    # subtitle.py
    "Subtitles have not been synthesized yet!": "还未合成任何字幕！",
    "The following subtitles are delayed due to the previous audio being too long.": "以下字幕由于之前的音频过长而被延迟",
    "Failed to synthesize the following subtitles or they were not synthesized": "以下字幕合成失败或未合成",
    # Settings
    "Failed to load settings, reset to default": "设置加载失败，恢复默认",
    "Error, Invalid Path": "错误，无效的路径",
    "Env detected": "已检测到环境",
    "Restarting...": "正在重启...",
    "An error occurred. Please restart manually!": "出现错误，请手动重启！",
    "Settings saved successfully!": "成功保存设置！",
    "Settings have been disabled!": "设置已被禁用",
    "Click Apply & Save for these settings to take effect.": "点击应用后，这些设置才会生效。",
    "General": "通用设置",
    "The port used by this program, 0=auto. When conflicts prevent startup, use -p parameter to specify the port.": "本程序所使用的端口 0=自动。当冲突无法启动时，使用参数-p来指定启动端口",
    "Enable LAN access. Restart to take effect.": "开启局域网访问,重启生效",
    "Overwrite history records with files of the same name instead of creating a new project.": "同名文件覆盖历史记录而不是新建工程",
    "Clear temporary files on each startup (which will also erase history records).": "每次启动时清除临时文件（会一并清除合成历史）",
    "Concurrency Count": "可同时处理多少请求",
    "Server Mode can only be enabled by modifying configuration file or startup parameters.": "服务模式，只能通过修改配置文件或启动参数开启",
    "Minimum voice interval (seconds)": "语音最小间隔(秒)",
    "Maximum audio acceleration ratio (requires ffmpeg)": "(慎用)音频最大加速倍率，尝试加速音频以和起止时间同步。要求安装ffmpeg",
    "Sampling rate of output audio, 0=Auto": "输出音频采样率，0=自动",
    "Remove inhalation and silence at the beginning and the end of the audio": "(实验功能)去除音频开头结尾的吸气声和静音",
    "Edit Panel Row Count (Requires a restart)": "编辑栏行数,重启生效",
    "Theme (Requires a restart)": "选择主题，重启后生效，部分主题可能需要科学上网",
    "Clear temporary files": "立即清除临时文件",
    "Submodule Settings": "子模块设置",
    "Python Interpreter Path for BV2": "设置BV2环境路径",
    "Root Path of BV2": "BV2项目根目录",
    "Start Parameters": "启动参数",
    "Downgrade API version to v1": "使用api_v1而不是v2",
    "Python Interpreter Path for GSV": "设置GSV环境路径",
    "Root Path of GSV": "GSV项目根目录",
    "Server Region": "服务区域",
    "KEY Warning: Key is stored in plaintext. DO NOT send the key to others or share your configuration file!": "密钥 警告:密钥明文保存，请勿将密钥发送给他人或者分享设置文件！",
    "Select required languages, separated by commas or spaces.": "筛选需要的语言，用逗号或空格隔开",
    "Translation Module": "翻译模块设置",
    "Default Request Address for Ollama": "Ollama默认请求地址",
    "Apply & Save": "应用并保存当前设置",
    "Restart UI": "重启UI",
    # TTS
    "An error has occurred. Please check if the API is running correctly. Details": "发生错误，请检查API是否正确运行。报错内容",
    "Advanced Parameters": "高级合成参数",
    "Generate Audio": "生成",
    # BV2
    "Select Speaker ID or Speaker Name": "选择说话人id或输入名称",
    # GSV(AR)
    "Returned Message": "返回信息",
    "Select TTS Project": "选择TTS项目",
    "Inference text language": "要合成的语言",
    "Main Reference Audio": "主参考音频",
    "Auxiliary Reference Audios": "辅参考音频",
    "Transcription of Main Reference Audio": "主参考音频文本",
    "Transcription | Pretrained Speaker (Cosy)": "参考音频文本|Cosy预训练音色",
    "Language of Main Reference Audio": "参考音频语言",
    "Model Path": "模型路径",
    "Switch Models": "模型切换",
    "Fragment Interval(sec)": "分段间隔(秒)",
    "How to cut": "怎么切",
    "(Optional) Description": "描述信息，可选",
    "Presets": "预设",
    "You must upload Main Reference Audio": "你必须指定主参考音频",
    "Preset saved successfully": "预设保存成功",
    "Failed to switch model": "模型切换失败",
    "Preset has been loaded.": "预设加载完毕",
    "Models are not switched. If you need to switch, please manually click the button.": "当前未切换模型,若需要强制切换请手动点击按钮",
    "Please specify the model path!": "请指定模型路径！",
    "Switching Models...": "正在切换模型...",
    "Model Paths seem to be invalid, which could lead to errors!": "模型路径可能无效，会导致切换错误！",
    "You have incorrectly entered a folder path!": "你错误地填写成了文件夹的路径！！！",
    "Models switched successfully": "模型已切换",
    "Error details": "报错内容",
    "Successfully deleted": "删除成功",
    "Please select a valid preset!": "请选择一个有效的预设！",
    "No preset available": "当前没有预设",
    "Partial auxiliary reference audio is missing!": "辅助参考音频存在丢失！",
    "DICT_LANGUAGE": {
        "中文": "all_zh",
        "粤语": "all_yue",
        "英文": "en",
        "日文": "all_ja",
        "韩文": "all_ko",
        "中英混合": "zh",
        "粤英混合": "yue",
        "日英混合": "ja",
        "韩英混合": "ko",
        "多语种混合": "auto",
        "多语种混合(粤语)": "auto_yue",
    },
    "CUT_METHOD": {
        "不切": "cut0",
        "凑四句一切": "cut1",
        "凑50字一切": "cut2",
        "按中文句号。切": "cut3",
        "按英文句号.切": "cut4",
        "按标点符号切": "cut5",
    },
    # MSTTS
    "Please fill in your key to get MSTTS speaker list.": "要获取微软TTS说话人列表,你必须先填写密钥！",
    "Can not get speaker list of MSTTS. Details": "无法下载微软TTS说话人列表。报错内容",
    "Failed to obtain access token from Microsoft.": "获取微软token出错",
    "Failed to obtain access token from Microsoft. Check your API key, server status, and network connection. Details": "获取微软token出错，检查密钥、服务器状态和网络连接。报错内容",
    "Can not access Microsoft TTS service. Check your API key, server status, and network connection. Details": "微软TTS出错，检查密钥、服务器状态和网络连接。报错内容",
    "Refresh speakers list": "刷新说话人列表",
    "Choose Language": "选择语言",
    "Choose Your Speaker": "选择你的说话人",
    "Style": "说话风格",
    "Role": "角色扮演",
    "Speed": "语速",
    "Pitch": "音调",
    "MSTTS_NOTICE": """使用微软TTS需要联网，请先前往设置页填入服务区和密钥才可以使用。请注意每个月的免费额度。<br>[【关于获取密钥：打开链接后请仔细阅读 先决条件 】](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech)""",
    "Please Select Your Speaker!": "请选择你的说话人！",
    "Please fill in your key!": "请配置密钥!",
    # custom api
    "Choose Custom API Code File": "选择自定义API代码文件",
    "No custom API code file found.": "当前没有自定义API预设",
    "Please select a valid custom API code file!": "请选择有效的API配置文件！",
    # Subtitle Translation
    "Start Translating": "开始翻译",
    "Translating": "正在翻译",
    "Failed to translate": "翻译失败",
    "Subtitle Translation": "字幕翻译",
    "Upload your subtitle files (multiple allowed).": "上传字幕(可多个)",
    "Send output files to Main Page": "发送至主页面",
    "Send output files to Translator": "发送至翻译页面",
    "Specify Target Language": "选择目标语言",
    "File Output Path": "文件输出路径",
    "Select Translator": "选择翻译器",
    # Ollama
    "Failed to get model list from Ollama": "Ollama获取模型列表失败",
    "You must specify the model!": "你必须指定模型！",
    "Select Your Model": "选择模型",
    "Unload Model": "卸载模型",
    "OLLAMA_NOTICE": "⚠️LLM在运行时会占用较多VRAM。使用完毕后不要忘了选择并卸载对应模型以释放显存！⚠️",
    # EXTENSIONS
    # WAV2SRT
    "Audio/Video Transcribe": "音视频转字幕",
    "Upload File": "上传文件",
    "Save Path(Folder Path), Default: SAVAdata\\output": "保存路径，填文件夹名，默认为SAVAdata\\output",
    "Python Interpreter Path, align with GSV by default": "Python解释器路径,默认和GSV一致",
    "Select ASR model. Funasr supports only Chinese(but much more faster) while Faster-Whisper has multi-language support": "选择ASR模型，funasr只支持中文但更快更准，faster whisper支持多语言",
    "(ms)Minimum length of each segment": "(ms)每段最小多长",
    "(ms)Minium slice interval": "(ms)最短切割间隔",
    "(ms)Minium silence length": "(ms)切完后静音最多留多长",
    "Other Parameters": "其他参数",
    "Start": "开始",
    "Stop": "停止",
    "Please upload audio or video!": "请上传音频文件！",
    "Please specify Python Interpreter!": "请指定解释器！",
    "Processing": "正在进行",
    "Tasks are terminated due to an error in": "任务出错,终止:",
    "Finished": "任务结束",
    "WAV2SRT_INFO": """
            本功能可直接用于GPT-SoVITS整合包，否则需要自己安装对应依赖。<br>
            # 其他参数：
            `--whisper_size` 默认:large-v3 | 使用faster whisper时指定模型<br>
            `--threshold` 默认:-40 | 音量小于这个值视作静音的备选切割点<br>
            `--hop_size` 默认:20 | 怎么算音量曲线，越小精度越大计算量越高（不是精度越大效果越好）<br>
            """,
}
