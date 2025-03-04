import os
import gradio as gr
import json
import Sava_Utils
import time
import os
import sys

import Sava_Utils.utils
from . import logger

current_path = os.environ.get("current_path")

# https://huggingface.co/datasets/freddyaboulton/gradio-theme-subdomains/resolve/main/subdomains.json
gradio_hf_hub_themes = [
    "default",
    "base",
    "glass",
    "soft",
    "gradio/monochrome",
    "gradio/seafoam",
    "gradio/dracula_test",
    "abidlabs/dracula_test",
    "abidlabs/Lime",
    "abidlabs/pakistan",
    "Ama434/neutral-barlow",
    "dawood/microsoft_windows",
    "finlaymacklon/smooth_slate",
    "Franklisi/darkmode",
    "freddyaboulton/dracula_revamped",
    "freddyaboulton/test-blue",
    "gstaff/xkcd",
    "Insuz/Mocha",
    "Insuz/SimpleIndigo",
    "JohnSmith9982/small_and_pretty",
    "nota-ai/theme",
    "nuttea/Softblue",
    "ParityError/Anime",
    "reilnuud/polite",
    "remilia/Ghostly",
    "rottenlittlecreature/Moon_Goblin",
    "step-3-profit/Midnight-Deep",
    "Taithrah/Minimal",
    "ysharma/huggingface",
    "ysharma/steampunk",
    "NoCrypt/miku",
]

class Settings:
    def __init__(
        self,
        server_port: int = 0,
        LAN_access:bool = False,        
        overwrite_workspace:bool = False,
        clear_tmp: bool = False,
        min_interval:float=0.3,
        num_edit_rows: int = 7,
        theme: str = "default",
        bv2_pydir: str = "",
        bv2_dir: str = "",
        bv2_args: str = "",
        gsv_pydir: str = "",        
        gsv_dir: str = "",        
        gsv_args: str = "",
        ms_region: str = "eastasia",
        ms_key: str = "",
        ms_lang_option: str="zh"
    ):
        self.server_port = int(server_port)
        self.LAN_access = LAN_access
        self.overwrite_workspace = overwrite_workspace
        self.clear_tmp = clear_tmp        
        self.min_interval = min_interval
        self.num_edit_rows = int(num_edit_rows)
        self.theme = theme
        self.ms_region = ms_region
        self.ms_key = ms_key
        self.ms_lang_option = ms_lang_option
        # detect python envs####
        if bv2_pydir != "":
            if os.path.exists(bv2_pydir):
                self.bv2_pydir = os.path.abspath(bv2_pydir)
            else:
                self.bv2_pydir = ""
                gr.Warning("错误：填写的路径不存在！")
        else:
            if (
                os.path.exists(os.path.join(current_path, "venv\\python.exe"))
                and "VITS2" in current_path.upper()
            ):
                self.bv2_pydir = os.path.join(current_path, "venv\\python.exe")
                logger.info("已检测到Bert-VITS2环境")
            else:
                self.bv2_pydir = ""

        if gsv_pydir != "":
            if os.path.exists(gsv_pydir):
                self.gsv_pydir = os.path.abspath(gsv_pydir)
            else:
                self.gsv_pydir = ""
                gr.Warning("错误：填写的路径不存在！")
        else:
            if (
                os.path.exists(os.path.join(current_path, "runtime\\python.exe"))
                and "GPT" in current_path.upper()
            ):
                self.gsv_pydir = os.path.join(current_path, "runtime\\python.exe")
                logger.info("已检测到GPT-SoVITS环境")
            else:
                self.gsv_pydir = ""
        ###################
        self.bv2_dir = bv2_dir
        self.gsv_dir = gsv_dir
        self.bv2_args = bv2_args
        self.gsv_args = gsv_args
        if self.bv2_pydir != "":
            if bv2_dir == "":
                self.bv2_dir = os.path.dirname(os.path.dirname(self.bv2_pydir))
        if self.gsv_pydir != "":
            if gsv_dir == "":
                self.gsv_dir = os.path.dirname(os.path.dirname(self.gsv_pydir))

    def to_dict(self):
        return self.__dict__

    def save(self):
        dict = self.to_dict()
        os.makedirs(os.path.join(current_path, "SAVAdata"), exist_ok=True)
        with open(
            os.path.join(current_path, "SAVAdata", "config.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(dict, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, dict):
        return cls(**dict)


def load_cfg():
    config_path = os.path.join(current_path, "SAVAdata", "config.json")
    if os.path.exists(config_path):
        try:
            config = Settings.from_dict(json.load(open(config_path, encoding="utf-8")))
            logger.info("成功加载自定义设置")
        except Exception as e:
            config = Settings()
            logger.warning(f"用户设置加载失败，恢复默认设置！{e}")
    else:
        config = Settings()
        logger.info("当前没有自定义设置")
    return config

def restart():
    gr.Warning("正在重启，如果更改了主题或端口，请关闭当前页面！")
    time.sleep(0.5)
    os.system("cls")
    if os.environ.get('exe')!='True':
        os.execl(sys.executable, f'"{sys.executable}"', f'"{sys.argv[0]}"')
    else:
        try:
            a = os.environ["_PYI_APPLICATION_HOME_DIR"]
            b = os.environ["_PYI_ARCHIVE_FILE"]
            c = os.environ["_PYI_PARENT_PROCESS_LEVEL"]
            os.unsetenv("_PYI_APPLICATION_HOME_DIR")
            os.unsetenv("_PYI_ARCHIVE_FILE")
            os.unsetenv("_PYI_PARENT_PROCESS_LEVEL")
            Sava_Utils.utils.run_command(command=f"{sys.executable}", dir=current_path)
            os.environ["_PYI_APPLICATION_HOME_DIR"] = a
            os.environ["_PYI_ARCHIVE_FILE"] = b
            os.environ["_PYI_PARENT_PROCESS_LEVEL"] = c
        except Exception as e:
            gr.Warning(f"出现错误{str(e)}，请手动重启！")
        os.system(f"taskkill /PID {os.getpid()} /F")

class Settings_UI():
    def __init__(self,componments:list):
        self.componments=componments
        self.ui=False

    def save_settngs(self,*args):
        current_edit_rows = Sava_Utils.config.num_edit_rows
        Sava_Utils.config = Settings(*args)
        Sava_Utils.config.save()
        for i in self.componments:
            i.update_cfg(config=Sava_Utils.config)
        if Sava_Utils.config.num_edit_rows != current_edit_rows:
            Sava_Utils.config.num_edit_rows = current_edit_rows
            logger.info("更改字幕栏数需要重启生效")
            gr.Info("更改字幕栏数需要重启生效")
        logger.info("成功保存设置！")
        gr.Info("成功保存设置！")
        return args

    def getUI(self):
        if not self.ui:
            self.ui = True
            return self._UI()
        else:
            raise "ERR"

    def _UI(self):
        gr.Markdown("⚠️点击应用后，这些设置才会生效。⚠️")
        with gr.Group():
            gr.Markdown(value="通用设置")
            with gr.Row():
                self.server_port=gr.Number(label="本程序所使用的默认端口，重启生效。0=自动。当冲突无法启动时，使用参数-p来指定启动端口",value=Sava_Utils.config.server_port,minimum=0,scale=3)
                self.LAN_access = gr.Checkbox(label="开启局域网访问,重启生效",value=Sava_Utils.config.LAN_access,scale=1)
            self.overwrite_workspace=gr.Checkbox(label="覆盖历史记录而不是新建工程",value=Sava_Utils.config.overwrite_workspace,interactive=True)
            self.clear_cache=gr.Checkbox(label="每次启动时清除临时文件（会一并清除合成历史）",value=Sava_Utils.config.clear_tmp,interactive=True)
            self.min_interval=gr.Slider(label="语音最小间隔(秒)",minimum=0,maximum=3,value=Sava_Utils.config.min_interval,step=0.1)
            self.num_edit_rows=gr.Number(label="重新抽卡页面同时展示的字幕数",minimum=1,maximum=20,value=Sava_Utils.config.num_edit_rows)                        
            self.theme = gr.Dropdown(choices=gradio_hf_hub_themes, value=Sava_Utils.config.theme, label="选择主题，重启后生效，部分主题可能需要科学上网",interactive=True)
            self.cls_cache_btn=gr.Button(value="立即清除临时文件",variant="primary")
        with gr.Group():
            gr.Markdown(value="BV2")
            self.bv2_pydir_input=gr.Textbox(label="设置BV2环境路径",interactive=True,value=Sava_Utils.config.bv2_pydir)
            self.bv2_dir_input=gr.Textbox(label="设置BV2项目路径,使用整合包可不填",interactive=True,value=Sava_Utils.config.bv2_dir)
            self.bv2_args=gr.Textbox(label="设置BV2启动参数",interactive=True,value=Sava_Utils.config.bv2_args)
        with gr.Group():
            gr.Markdown(value="GSV")
            self.gsv_pydir_input=gr.Textbox(label="设置GSV环境路径",interactive=True,value=Sava_Utils.config.gsv_pydir)
            self.gsv_dir_input=gr.Textbox(label="设置GSV项目路径,使用整合包可不填",interactive=True,value=Sava_Utils.config.gsv_dir)
            self.gsv_args=gr.Textbox(label="设置GSV-API启动参数",interactive=True,value=Sava_Utils.config.gsv_args)
        with gr.Group(): 
            gr.Markdown(value="微软TTS")
            self.ms_region=gr.Textbox(label="服务区域",interactive=True,value=Sava_Utils.config.ms_region)
            self.ms_key=gr.Textbox(label="密钥 警告:密钥明文保存，请勿将密钥发送给他人或者分享设置文件！",interactive=True,value=Sava_Utils.config.ms_key) 
            self.ms_lang_option=gr.Textbox(label="筛选需要的语言，用逗号或空格隔开",interactive=True,value=Sava_Utils.config.ms_lang_option)
        self.save_settings_btn=gr.Button(value="应用并保存当前设置",variant="primary")
        self.restart_btn = gr.Button(value="重启UI", variant="stop")

        self.cls_cache_btn.click(Sava_Utils.utils.cls_cache,inputs=[],outputs=[])

        componments_list=[
            self.server_port,
            self.LAN_access,
            self.overwrite_workspace,
            self.clear_cache,
            self.min_interval,
            self.num_edit_rows,
            self.theme,
            self.bv2_pydir_input,
            self.bv2_dir_input,
            self.bv2_args,
            self.gsv_pydir_input,
            self.gsv_dir_input,
            self.gsv_args,
            self.ms_region,
            self.ms_key,
            self.ms_lang_option,
        ]

        self.save_settings_btn.click(self.save_settngs,inputs=componments_list,outputs=componments_list)
        self.restart_btn.click(restart,[],[])
